# 🚀 PCB Backend API - Unit Testing Branch

> **Note**: This is the dedicated branch for **setup and validation of unit tests**.  
> If you are looking for the production documentation, please switch to the `main` branch.

This branch focuses on ensuring code stability and reliability using `pytest` with a **Mocked Environment** strategy.

---

## 🧪 Testing Features
This branch implements a robust testing suite that covers:
*   **Auto-Registration**: Validates ESP32 device registration flow.
*   **Device Claiming**: Ensures user ownership claim logic works safely.
*   **Mqtt Controls**: Mocks MQTT publishing to verify command logic without real broker connection.
*   **Rate Limiting**: Tests protection mechanisms against spamming.

### Why Mocking?
We use `mock` and `patch` to isolate the backend from external dependencies:
1.  **NO Real Database**: Uses `sqlite:///:memory:` for fast, clean-slate testing.
2.  **NO Real MQTT**: Connection is intercepted to prevent network errors.
3.  **NO Real Redis**: Rate limits are bypassed or mocked for consistent results.

---

## 📋 Prerequisites
Ensure you have the following installed:
1.  **Python 3.11+**
2.  **Virtual Environment (`venv`)**

---

## 🚀 Setup & Installation

### 1. Clone & Switch Branch
```bash
git clone https://github.com/username/API-PCB.git
cd API-PCB
git checkout unit-testing
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Requirements
Install main dependencies + testing libraries (`pytest`, `httpx`, etc.):
```bash
pip install -r requirements.txt
```

---

## ⚙️ Running Tests

### Standard Run
Simply execute `pytest` from the root directory. It will automatically load configuration from `tests/conftest.py`.

```bash
pytest
```

**Expected Output (Greens):**
```
tests/test_devices.py ...... [100%]
================= 6 passed in 0.xxs =================
```

### Run with Detailed Output
To see printed logs (e.g. "Mock MQTT Publish"):
```bash
pytest -s
```

### Run Specific Test
```bash
pytest tests/test_devices.py::test_auto_register_success
```

---

## 📂 Test Structure
*   **`tests/`**: Contains all test modules.
    *   **`conftest.py`**: The heart of the test setup. Contains:
        *   `load_dotenv()`: Auto-load `.env` variables.
        *   `mock_external_services`: Fixture to patch MQTT, Redis, Firebase.
        *   `db_session`: Fixture to create/drop pure in-memory SQLite tables.
    *   **`test_devices.py`**: Functional tests for device endpoints.

---

## 🔧 Troubleshooting
If tests fail:
1.  **Check `.venv`**: Ensure it's active (`source .venv/bin/activate`).
2.  **Requirements**: Run `pip install -r requirements.txt` again.
3.  **Environment**: `conftest.py` should handle env vars, but ensure `.env` file exists if your app code critically depends on checking file existence.

---

**Happy Testing!** 🧪
