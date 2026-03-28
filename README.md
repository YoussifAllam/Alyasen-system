# Alyasen System ERP

Welcome to the **Alyasen System ERP** project. This is a comprehensive, feature-rich desktop Enterprise Resource Planning application built with Python and **PyQt5**. The system is designed to streamline administrative tasks, manage clients, monitor projects, track company finances, assets, and personnel, and handle end-to-end operational workflows efficiently. 

## About Project

The Alyasen System is designed to manage various facets of enterprise and business operations within a robust and interactive desktop user interface. 
Key functionalities include:
- **Authentication & Authorization**: Secure login mechanisms with permission controls.
- **Client & Supplier Management**: Maintain rich profiles, communication logs, and associated records.
- **Project Tracking**: Dedicated hubs to track ongoing projects, including scopes, deliverables, and linked contracts.
- **Financial Control**: Manage company safe logs, transactions, expenses, and quotations with precision.
- **Reports & Logging**: Generate business intelligence reports and keep secure program activity logs.
- **Dynamic Theming**: Support for multiple visual styles to adapt to user preferences.

---

## Project Architecture

### Backend Architecture Note
> **Note**: The complete, in-depth architectural breakdown of the backend system (Django, API endpoints, Models, and Database Schema) is maintained in a separate repository. Please refer to the backend repository documentation for full server-side context.
https://github.com/YoussifAllam/Django-Project-Architecture
### Frontend Application Architecture (PyQt5)

The desktop client is modularly designed around clean separation of concerns. The interface is composed of multiple dynamic modules loaded into a main window container (Stacked Widget), utilizing reusable UI elements and centralized stylesheets.

Here is a detailed tree explaining the core architecture of the PyQt5 Application layer:

```text
Alyasen-system/
└── PyQt5/
    ├── main.py                     # Entry point of the PyQt5 application. Bootstraps the app, loads styles, and initializes the Main Window.
    ├── requirements.txt            # Python dependencies necessary to run and build the application (PyQt5, requests, etc.).
    ├── setup.iss                   # Inno Setup configuration script for compiling a deployable Windows installer.
    │
    ├── components/                 # The core directory housing all UI modules, dialogs, and specific business logic.
    │   ├── __init__.py             
    │   ├── Auth/                   # Authentication logic, Login UI screens, and session management.
    │   ├── dashboard/              # The central overview dashboard displaying analytical charts, quick stats, and primary application metrics.
    │   ├── clients/                # Modules dealing with Client management, including rich profiles, client history, and specific client actions.
    │   ├── projects/               # Project management interfaces, project entry forms, and detailed project state viewing.
    │   ├── suppliers/              # Tools for adding, modifying, and interacting with supplier data and related external contracts.
    │   ├── quotations/             # Quotations generation, data tables to view historical quotes, and client alignment logic.
    │   ├── Company_assets/         # Dedicated UI representing the company's internal assets, tracking conditions, and assignments.
    │   ├── Workers/                # Management of labor resources, worker profiles, and associated data forms.
    │   │
    │   ├── Main_Ui_Components/     # The functional backbone containing core reusable UI elements across the app.
    │   │   ├── main_window.py      # The root window integrating the Navigation Sidebar and the main central Stacked Widget for routing.
    │   │   ├── sidebar.py          # The interactive side-navigation component handling module switching across the system.
    │   │   ├── stylesheet.py       # Centralized Application-wide styling directives (Primary / Dark Theme CSS-like configurations).
    │   │   ├── light_stylesheet.py # Application-wide styling directives representing the alternate Light Theme.
    │   │   └── constant.py         # Application-wide predefined static values, enums, dimensions, and configuration strings.
    │   │
    │   ├── ui_company_safe.py      # A specific UI tool managing the financial tracking of the physical/digital company safe logs and transactions.
    │   ├── ui_expenses.py          # Comprehensive expense management, allowing entry and categorization of company-wide overheads.
    │   ├── notifications_dialog.py # The alert and notification system dialog, providing real-time user feedback and action tracking.
    │   ├── program_log.py          # Activity logging module, surfacing application logs, errors, and system states to administrators.
    │   └── reports.py              # Logic dealing with the aggregation, formatting, and export of different administrative reports.
    │
    └── resources/                  # Directory containing static UI assets. Includes icons, logos, fonts, branding materials, and graphical placeholders.
```

---

## Code Writing Style

Maintaining clean, readable, and consistent code is a top priority for this project. We enforce standard Python guidelines using established community tools.

1. **PEP 8 Compliance**: The codebase is strictly written following Python enhancements proposals (PEP 8).
2. **Black Formatter**: All Python files must be formatted using `black` (The Uncompromising Code Formatter). This ensures 100% uniformity across files, removing developer-specific styling debates.
   - Run `black .` at the root of the project to format all code before committing.
3. **Flake8 Linter**: Code quality, unused imports, logical flow analysis, and PEP 8 alignment is checked using `flake8`.
   - Run `flake8` at the root. We aim for zero warnings to ensure operational robustness.
   - Settings for flake8 can be found or customized in `.flake8`.

---

## Comment Style

Clear documentation is required for all components.

- **Module-Level Docstrings**: Every module should explain its core responsibility at the very top.
- **Class and Function Docstrings**: We use descriptive multi-line docstrings (Google or Sphinx style) for every class and function, detailing:
  - < type >(< scope >): < short summary in imperative mood>
  - [Optional body: explain the WHY, not the HOW. Wrap at 72 chars.]
  - [Optional footer: reference Issue IDs, Breaking Changes, or Co-authors]
- **Inline Comments**: Kept to a minimum and reserved strictly for explaining "Why" an unusual or highly complex 
implementation exists. Do not explain "What" the code is doing if it is self-evident.
- **TODOs**: Use `TODO(AuthorName): Date - Description` for pending features or refactoring tasks. 

---

## Setup & Execution Guide

Follow these steps to set up the project on your local machine and run it for development purposes.

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Clone the Repository
Clone this repository to your local workspace:
```bash
git clone https://github.com/YoussifAllam/Alyasen-system.git
cd Alyasen-system
```

### 3. Create a Virtual Environment
It is highly recommended to isolate dependencies utilizing a Python virtual environment.
```bash
python3 -m venv venv
```

### 4. Activate the Virtual Environment
- **Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

### 5. Install Requirements
Navigate to the `PyQt5` folder where the dependency file is stored and install required packages:
```bash
cd PyQt5
pip install -r requirements.txt
```

### 6. Run the Application
You can now start the ERP desktop application via the main entry point:
```bash
python main.py
```

---

## API Documentation

The desktop application heavily interacts with various backend endpoints to source and mutate data. 
- The full API Documentation (detailing routes, parameters, responses, and authentication tokens) is documented extensively using /OpenAPI.

---

## Application Screens (UI Snapshots)

*This section is dedicated to high-level visual documentation of the desktop app. Place relevant screenshots here to provide a quick visual understanding of module layouts.*

### Main Dashboard
<!-- Replace with actual image path -->
![Main Dashboard UI](./screenshots/placeholder_dashboard.png)

*Displays analytical charts, summary cards, and recent system activities.*

### Client Profile Manager
<!-- Replace with actual image path -->
![Client Profile UI](./screenshots/placeholder_client.png)

*Shows detailed layout of the client data, related projects, and direct fast-action tools.*

### Projects Tracking Module
<!-- Replace with actual image path -->
![Projects Module UI](./screenshots/placeholder_projects.png)

*Illustrates data tables and project specific forms with contract upload mechanics.*

### Quotations Interface
<!-- Replace with actual image path -->
![Quotations UI](./screenshots/placeholder_quotations.png)

*Demonstrates the dynamic table rendering quotation prices, client associations, and validity states.*

---

## Technical Notes & Additional Information

- **Executable Generation**: This project is configured to be compiled into a standalone Windows installer using Inno Setup (`setup.iss`) coupled with PyInstaller. This ensures standard users do not need Python environments to run the software.
- **Dynamic Routing**: The `main_window.py` acts precisely like frontend browser routing, utilizing the powerful `QStackedWidget` to mount and unmount views based on sidebar interactions without spawning multiple window processes.
- **Centralized Data Refreshing**: Ensure to call backend refetch queries strictly inside lifecycle methods within your UI components or rely on proper signal-slot connections triggering refresh methods on successful API posts. 

For further queries on the development environment, contact the core development team.
