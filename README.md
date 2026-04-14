## 当前功能
- 解析 PropertyGuru listing 文本
- 自动提取：
  - Project
  - Address
  - Area (Dxx)
  - Nearest MRT
  - Price / Size / PSF
  - Bedrooms / Bathrooms
  - Tenure / TOP
  - Developer / Total Units
  - URL（自动清洗）
- 写入 Google Sheet
- 如果第一行不是 Project，自动补 header

## 手动维护字段
Google Sheet 里保留以下手动维护列：
- Status
- Viewing Date
- Remarks

### Status 选项
- New
- Not Viewed
- Viewing Planned
- Viewed
- Interested
- Not Suitable
- Expired/Sold