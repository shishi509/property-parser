# 🏠 Property Listing Parser

一个用于快速解析 PropertyGuru 房源信息的小工具（Streamlit App）。

---

## 🚀 功能

* 粘贴房源信息（listing text）
* 自动提取：

  * Project 名
  * Address
  * District (Dxx)
  * 最近 MRT
  * Price / Size / PSF
  * Bedrooms / Bathrooms
  * Tenure / TOP
  * Developer / Total Units
  * URL
* 自动去重（避免重复记录）
* 保存到本地 CSV 数据库

---

## 🧠 使用方法（最重要）

### 1️⃣ 启动 App

```bash
python3 -m streamlit run app.py
```

---

### 2️⃣ 输入内容

👉 从 PropertyGuru 复制：

* listing 主页面信息
* Property details 弹窗
* 可选：project description（用于抓 District）

👉 粘贴进输入框

---

### 3️⃣ 点击按钮

* Extract → 查看结果
* Save to database → 存入 CSV

---

## 📁 数据存储

数据保存在：

```text
property_records.csv
```

功能：

* 自动去重（基于 URL）
* 自动追加新记录

---

## 🧩 数据来源说明

由于 PropertyGuru 页面结构不稳定：

👉 当前策略：

* 结构化数据（价格/面积等） → regex 提取
* District → 优先从描述中提取（"District xx"）
* MRT → 从文本中识别 "XXX MRT"

---

## ⚠️ 已知限制

* 不支持直接 URL 抓取（需要手动复制内容）
* District 依赖描述文本（可能缺失）
* MRT 信息格式不统一

---

## 🔄 后续可优化

* URL 自动抓取（scraping）
* District mapping（postal code → Dxx）
* UI 优化（批量输入）

---

## 🧑‍💻 作者

Shishi509（vibe coding 😄）
