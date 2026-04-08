# Alyasen System Database ERD

## Overview

This ERD represents the database schema for the Alyasen management system.

## Mermaid ERD Diagram

```mermaid
erDiagram
    User ||--|| Profile : "1-1"
    User {
        uuid uuid PK
        string name
        string username UK
        string email
        boolean email_verified
        integer otp
        datetime otp_created_at
        date created_date
        datetime last_login
        boolean is_approvid
        string user_type
    }
    Profile {
        int user_id PK
        string reset_password_token
        datetime reset_password_expire
    }

    Client ||--o{ ClientProjectBalance : "1-M"
    Client {
        int id PK
        string name
        string phone
        string email
        float total_balance_owed_to_us
        float total_remaining_balance_owed_to_us
        float total_paid_amount
        image profile_picture
    }

    Supplier ||--o{ SupplierProjectBalance : "1-M"
    Supplier ||--o{ CampaineItem : "1-M"
    Supplier ||--o{ MaterialsSuppliers : "1-M"
    Supplier ||--o{ SupplierProjectPayment : "1-M"
    Supplier {
        int id PK
        string name
        string phone
        string email
        float total_amount_due
        float total_amount_payable
        float total_paid_amount
        image profile_picture
    }

    BaseProject ||--o| RentProjects : "1-1"
    BaseProject ||--o| SellingIndustrialProjectDetails : "1-1"
    BaseProject ||--o{ ClientProjectBalance : "1-M"
    BaseProject ||--o{ SupplierProjectBalance : "1-M"
    BaseProject ||--o{ CampaineItem : "1-M"
    BaseProject ||--o{ ProjectContracts : "1-M"
    BaseProject ||--o{ ProjectsGuaranteeCheques : "1-M"
    BaseProject }o--|| Client : "M-1"
    BaseProject }o--|| Supplier : "M-1"
    BaseProject {
        int id PK
        string name
        string project_type
        int client_id FK
        string project_status
        float cost
        int supplier_id FK
        date created_date
    }

    RentProjects ||--o{ RentProjectOperationgCost : "1-M"
    RentProjects ||--o{ RentProjectContracts : "1-M"
    RentProjects ||--o{ ProjectRentalAds : "1-M"
    RentProjects {
        int id PK
        int project_id FK UK
        float operating_costs
        string project_status
        float value_added_tax
        float insurance_tax
        date insurance_tax_date
        float commercial_profits_tax
        float total_cost
        float net_profit
        float selling_price
    }

    RentProjectOperationgCost {
        int id PK
        int project_id FK
        string name
        float amount
    }

    RentProjectContracts {
        int id PK
        int project_id FK
        file contract
    }

    ProjectRentalAds {
        int id PK
        int project_id FK
        string ad_type
        int number
        string size
        string address
        text notes
    }

    SellingIndustrialProjectDetails ||--o{ IndustrialProjectOperationgCost : "1-M"
    SellingIndustrialProjectDetails ||--o{ MaterialsSuppliers : "1-M"
    SellingIndustrialProjectDetails ||--o{ IndustrialProjectContracts : "1-M"
    SellingIndustrialProjectDetails {
        int id PK
        int project_id FK UK
        float total_cost
        float total_materials_cost
        float profit
        float operating_costs
        float value_added_tax
        float insurance_tax
        date insurance_tax_date
        float profits_tax
    }

    IndustrialProjectOperationgCost {
        int id PK
        int project_id FK
        string name
        float amount
    }

    MaterialsSuppliers ||--o{ MaterialsSuppliersPayments : "1-M"
    MaterialsSuppliers {
        int id PK
        int project_id FK
        string name
        string phone
        string material_name
        float price
        float quantity
    }

    MaterialsSuppliersPayments {
        int id PK
        int m_supplier_id FK
        float amount
        date date
    }

    IndustrialProjectContracts {
        int id PK
        int project_id FK
        file contract
    }

    ProjectContracts {
        int id PK
        int project_id FK
        file contract
    }

    ProjectsGuaranteeCheques {
        int id PK
        int project_id FK
        string cheque_number
        date cheque_date
        float cheque_amount
    }

    ClientProjectBalance ||--o{ ClientProjectPayment : "1-M"
    ClientProjectBalance ||--o|| Campaine : "M-1"
    ClientProjectBalance {
        int id PK
        int client_fk_id FK
        int project_fk_id FK
        int campaine_fk_id FK
        string project_type
        float total
        float paid
        float remining
    }

    ClientProjectPayment {
        int id PK
        int client_project_balance_fk_id FK
        string portal_invoice_number
        file portal_invoice_file
        float payment_amount
        date payment_date
        string payment_type
        date check_cleared_date
        boolean is_cleared
        text notes
    }

    SupplierProjectBalance ||--o{ SupplierProjectPayment : "1-M"
    SupplierProjectBalance {
        int id PK
        int supplier_fk_id FK
        int project_fk_id FK
        float total
        float paid
        float remining
    }

    SupplierProjectPayment {
        int id PK
        int supplier_fk_id FK
        int project_fk_id FK
        string portal_invoice_number
        file portal_invoice_file
        float payment_amount
        date payment_date
        text notes
    }

    Campaine ||--o{ CampaineItem : "1-M"
    Campaine ||--o{ ClientProjectBalance : "1-M"
    Campaine }o--|| Client : "M-1"
    Campaine {
        int id PK
        string name
        int client_id FK
        float total_cost
        date created_date
    }

    CampaineItem {
        int id PK
        int campaine_id FK
        int supplier_id FK
        int project_id FK
    }

    Safe ||--o{ SafeLogs : "1-M"
    Safe {
        int id PK
        float balance
    }

    SafeLogs {
        int id PK
        text transaction
        datetime date
    }

    CompanyAssets ||--o{ CompanyAssetsAttachments : "1-M"
    CompanyAssets {
        int id PK
        string name
        float price
    }

    CompanyAssetsAttachments {
        int id PK
        int asset_id FK
        file file
    }

    Quotations ||--o{ QuotationsAttachments : "1-M"
    Quotations {
        int id PK
        string client_name
        string company_name
        float price
        text details
        date quotation_last_date
        datetime created_date
    }

    QuotationsAttachments {
        int id PK
        int quotation_id FK
        file attachment
    }

    Expenses {
        int id PK
        text transaction
        string permit_number
        float amount
        date created_date
        text notes
    }

    TransactionsLog {
        int id PK
        string username
        text transaction
        date created_date
    }

    Notification {
        int id PK
        uuid uuid UK
        string title
        text message
        boolean is_read
        datetime created_at
    }
```

## Table Summary

| Table | Description | Key Fields |
|-------|-------------|------------|
| **User** | System users (Admin, Accountant) | uuid PK, username UK |
| **Profile** | User profile info (password reset) | user_id PK FK |
| **Client** | Customer/client records | id PK |
| **Supplier** | Vendor/supplier records | id PK |
| **BaseProject** | Core project table | id PK, project_type |
| **RentProjects** | Rental project details | project_id FK UK |
| **SellingIndustrialProjectDetails** | Industrial project details | project_id FK UK |
| **ClientProjectBalance** | Client payment tracking | client_fk, project_fk, campaine_fk |
| **ClientProjectPayment** | Individual client payments | client_project_balance_fk FK |
| **SupplierProjectBalance** | Supplier payment tracking | supplier_fk, project_fk |
| **SupplierProjectPayment** | Individual supplier payments | supplier_fk FK |
| **Campaine** | Marketing campaigns | id PK, client FK |
| **CampaineItem** | Campaign line items | campaine FK, supplier FK, project FK |
| **Safe** | Company safe/treasury | id PK |
| **SafeLogs** | Safe transaction history | id PK |
| **CompanyAssets** | Fixed assets inventory | id PK |
| **CompanyAssetsAttachments** | Asset documents | asset FK |
| **Quotations** | Sales quotations | id PK |
| **QuotationsAttachments** | Quotation documents | quotation FK |
| **Expenses** | Company expenses | id PK |
| **TransactionsLog** | User activity log | id PK, username |
| **Notification** | System notifications | uuid PK UK |

## Key Relationships

1. **Client ↔ Project**: Through BaseProject.client FK (many projects per client)
2. **Supplier ↔ Project**: Through BaseProject.supplier FK (many projects per supplier)
3. **BaseProject ↔ RentProjects**: One-to-One (project_type='rent')
4. **BaseProject ↔ SellingIndustrialProjectDetails**: One-to-One (project_type='industrial')
5. **Client ↔ Campaine**: One-to-Many
6. **Campaine ↔ BaseProject**: Through CampaineItem (many-to-many)
7. **ClientProjectBalance**: Links Client, Project, and Campaine with payment tracking
8. **SupplierProjectBalance**: Links Supplier and Project with payment tracking
