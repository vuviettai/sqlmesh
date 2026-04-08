"""Transform records from staging_db.Facilities into sqlmesh_work.stg_btxh_facilities."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import flatten_facility
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "facility_id": "text",
    "facility_code": "text",
    "facility_name": "text",
    "su_kien": "text",
    "is_active": "boolean",
    "phien_ban": "bigint",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "created_by": "text",
    "updated_by": "text",
    "email": "text",
    "phone_number": "text",
    "fax": "text",
    "website": "text",
    "notes": "text",
    "contact_address": "text",
    "ward_code": "text",
    "province_id": "text",
    "province_code": "text",
    "nationality": "text",
    "nationality_code": "text",
    "area_type_code": "text",
    "center_type_id": "text",
    "center_type_code": "text",
    "center_type_name": "text",
    "facility_form": "text",
    "facility_form_name": "text",
    "license_status": "text",
    "management_unit_id": "text",
    "management_unit_code": "text",
    "management_unit_name": "text",
    "management_unit_type_id": "text",
    "director_name": "text",
    "director_birth_date": "date",
    "director_identity_number": "text",
    "director_document_type": "text",
    "director_document_type_code": "text",
    "decision_date": "date",
    "establishment_decision": "text",
    "establishment_year": "text",
    "total_area": "text",
    "total_staff": "text",
    "planned_capacity": "text",
    "total_beneficiaries": "text",
    "avg_area_per_beneficiary": "text",
    "avg_housing_area_per_beneficiary": "text",
    "service_target_ids": "text",
    "service_target_codes": "text",
}

TIMESTAMP_COLUMNS = ("_airbyte_extracted_at", "created_at", "updated_at")
DATE_COLUMNS = ("director_birth_date", "decision_date")
INTEGER_COLUMNS = ("_airbyte_generation_id", "phien_ban")
FETCH_BATCH_SIZE = 5_000


def _normalize_dataframe(records: list[dict[str, t.Any]]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records)
    df = df.reindex(columns=MODEL_COLUMNS.keys())

    for col in TIMESTAMP_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    for col in INTEGER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    return df.astype(object).where(pd.notna(df), None)


@model(
    "sqlmesh_work.stg_btxh_facilities",
    description=(
        "Cleaned and flattened BTXH facility records from the staging "
        'PostgreSQL table public."Facilities" into the BI database.'
    ),
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="updated_at", batch_size=90),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["facility_id"],
    columns=MODEL_COLUMNS,
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> t.Iterator[pd.DataFrame]:
    del context, execution_time, kwargs

    load_dotenv_if_present()
    conn = get_connection()
    try:
        schema_name = os.environ.get("STAGING_DB_SCHEMA", "public")
        table_name = os.environ.get("STAGING_BTXH_FACILITY_SOURCE_TABLE", "Facilities")
        query = sql.SQL(
            """
            SELECT
                _airbyte_raw_id,
                _airbyte_extracted_at,
                _airbyte_generation_id,
                id,
                fax,
                email,
                notes,
                active,
                "suKien",
                website,
                "phienBan",
                "wardCode",
                "createdAt",
                "createdBy",
                "totalArea",
                "updatedAt",
                "updatedBy",
                "provinceId",
                "totalStaff",
                "createdAtmm",
                nationality,
                "phoneNumber",
                "updatedAtmm",
                "areaTypeCode",
                "centerTypeId",
                "decisionDate",
                "directorName",
                "facilityCode",
                "facilityForm",
                "facilityName",
                "provinceCode",
                "licenseStatus",
                "centerTypeCode",
                "centerTypeName",
                "contactAddress",
                "nationalityCode",
                "plannedCapacity",
                "facilityFormName",
                "managementUnitId",
                "serviceTargetIds",
                "directorBirthDate",
                "establishmentYear",
                "managementUnitCode",
                "managementUnitName",
                "serviceTargetCodes",
                "totalBeneficiaries",
                "directorDocumentType",
                "managementUnitTypeId",
                "avgAreaPerBeneficiary",
                "establishmentDecision",
                "directorIdentityNumber",
                "directorDocumentTypeCode",
                "avgHousingAreaPerBeneficiary"
            FROM {schema}.{table}
            WHERE COALESCE(
                TO_TIMESTAMP("updatedAt" / 1000.0),
                TO_TIMESTAMP(NULLIF("updatedAtmm", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
            ) >= %(start)s
              AND COALESCE(
                TO_TIMESTAMP("updatedAt" / 1000.0),
                TO_TIMESTAMP(NULLIF("updatedAtmm", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
              ) < %(end)s
            """
        ).format(schema=sql.Identifier(schema_name), table=sql.Identifier(table_name))

        with conn.cursor() as cur:
            cur.execute(query, {"start": start, "end": end})
            while True:
                rows = cur.fetchmany(FETCH_BATCH_SIZE)
                if not rows:
                    break

                records = [flatten_facility(dict(row)) for row in rows]
                yield _normalize_dataframe(records)
    finally:
        conn.close()
