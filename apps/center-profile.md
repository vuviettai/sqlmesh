# 📄 API Documentation: GET /center-profiles

## 🔹 1. Tổng quan

* **Endpoint:** `GET /center-profiles`
* **Mô tả:** API dùng để **tìm kiếm và phân trang hồ sơ đối tượng** trong các cơ sở trợ giúp xã hội.
* **Phương thức:** `GET`
* **Content-Type:** `application/json`

---

## 🔹 2. Query Parameters

### 📌 2.1. Phân trang (bắt buộc)

| Tên              | Kiểu    | Bắt buộc | Mô tả                   |
| ---------------- | ------- | -------- | ----------------------- |
| pageRequest.page | integer | ✅        | Số trang (bắt đầu từ 0) |
| pageRequest.size | integer | ✅        | Số bản ghi mỗi trang    |

📌 Ví dụ:

```http
pageRequest.page=0&pageRequest.size=10
```

---

### 📌 2.2. Bộ lọc dữ liệu

#### 🔸 objectTypeCode

* **Kiểu:** `array[string]`
* **Mô tả:** Lọc theo loại đối tượng

| Code | Mô tả                                   |
| ---- | --------------------------------------- |
| L01  | Trẻ em                                  |
| L02  | Người cao tuổi                          |
| L03  | Người khuyết tật                        |
| L04  | Người nhiễm HIV/AIDS                    |
| L05  | Nạn nhân cần bảo vệ khẩn cấp            |
| L06  | Đối tượng cần bảo vệ khẩn cấp khác      |
| L07  | Đối tượng theo xử lý vi phạm hành chính |
| L08  | Tự nguyện                               |
| L09  | Người tâm thần                          |
| L10  | Đối tượng khác                          |

📌 Ví dụ:

```http
objectTypeCode=L01&objectTypeCode=L02
```

---

#### 🔸 objectGroupCode

* **Kiểu:** `string`
* **Mô tả:** Lọc theo nhóm đối tượng

| Code | Mô tả                       |
| ---- | --------------------------- |
| N01  | Hoàn cảnh đặc biệt khó khăn |
| N02  | Cần bảo vệ khẩn cấp         |
| N03  | Không còn khả năng lao động |
| N04  | Tự nguyện                   |
| N05  | Chưa thể hòa nhập cộng đồng |
| N06  | Khác                        |

📌 Ví dụ:

```http
objectGroupCode=N02
```

---

#### 🔸 gender

* **Kiểu:** `string`
* **Mô tả:** Giới tính (NAM,NU,KHAC)

---

#### 🔸 facilityId

* **Kiểu:** `UUID`
* **Mô tả:** ID cơ sở trợ giúp xã hội

---

#### 🔸 organizationId

* **Kiểu:** `UUID`
* **Mô tả:** ID tổ chức quản lý

---

#### 🔸 facilityForm

* **Kiểu:** `string`
* **Mô tả:** Hình thức cơ sở

| Giá trị        | Mô tả          |
| -------------- | -------------- |
| CONG_LAP       | Công lập       |
| NGOAI_CONG_LAP | Ngoài công lập |

---

#### 🔸 stayType

* **Kiểu:** `string`
* **Mô tả:** Loại hình lưu trú

| Giá trị        | Mô tả          |
| -------------- | -------------- |
| NOI_TRU        | Nội trú        |
| BAN_TRU        | Bán trú        |
| NGOAI_TRU      | Ngoại trú      |

---

#### 🔸 isArchived

* **Kiểu:** `boolean`
* **Mặc định:** 0
* **Mô tả:** Trạng thái lưu trữ hồ sơ các hồ sơ đang mở (false) đã đóng true

---

#### 🔸 search

* **Kiểu:** `string`
* **Mô tả:** Tìm kiếm theo từ khóa (tên, mã hồ sơ, CCCD, ...)

---

## 🔹 3. Ví dụ Request

```http
GET /center-profiles?pageRequest.page=0&pageRequest.size=10
  &objectTypeCode=L01
  &objectGroupCode=N01
  &facilityForm=CONG_LAP
  &isArchived=false
  &search=Nguyen
```

---

## 🔹 4. Response

### 📌 Thành công (200 OK)

```json
{
  "content": [
    {
      "id": "uuid",
      "name": "Nguyễn Văn A",
      "objectTypeCode": "L01",
      "objectGroupCode": "N01",
      "gender": "MALE",
      "facilityId": "uuid",
      "status": "ACTIVE"
    }
  ],
  "page": 0,
  "size": 10,
  "totalElements": 100,
  "totalPages": 10
}
```