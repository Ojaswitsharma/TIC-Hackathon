# TIC System - Quick Start Guide

## 📋 How to Use (Default Mode)

### Step 1: Place JSON Files
Put your customer data JSON files in the `input/` directory:

```json
{
  "customer_info": {
    "name": "Customer Name",
    "phone": "1234567890",
    "email": "customer@email.com"
  },
  "complaint_details": {
    "description": "Issue description here",
    "category": "Delivery Issue|Billing Issue|Product Issue|Refund Request",
    "urgency_level": "low|medium|high|critical",
    "order_id": "ORDER123",
    "product_name": "Product Name"
  },
  "company_info": {
    "company_name": "Your Company"
  },
  "status": "conversation_completed"
}
```

### Step 2: Run the System
```bash
python main.py
```

### Step 3: Get Results
- ✅ Processed results saved to `output/` directory
- 📦 Original files moved to `input/processed/`
- 🔍 Each result contains case ID, resolution message, and procedural plan

## 📁 Directory Structure
```
TIC/
├── input/               # Place your JSON files here
│   └── processed/       # Processed files moved here
├── output/              # Results saved here
├── documents/           # Company documents for knowledge base
└── main.py             # Run this file
```

## 🎯 Supported Categories
- **Delivery Issue**: Missing packages, delivery problems
- **Billing Issue**: Billing disputes, duplicate charges
- **Product Issue**: Defective products, quality issues  
- **Refund Request**: Refund processing, cancellations

## 🚨 Urgency Levels
- **low**: Standard processing (0.3)
- **medium**: Normal priority (0.6)
- **high**: High priority (0.9)
- **critical**: Urgent processing (1.0)

## 📊 Output Format
Each processed case generates a JSON result with:
- `status`: "resolved" or "error"
- `case_id`: Unique case identifier
- `priority`: Determined priority level
- `resolution_message`: Complete customer response
- `procedural_plan`: Detailed step-by-step plan
