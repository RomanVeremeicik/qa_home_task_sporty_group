# QA Automation Assignment — Twitch Web UI + Public APIs

This repository contains automated tests for:

- **Twitch mobile E2E UI Flow** using Selenium  
- **Public API Tests** using Pytest + Requests  
- **Allure Reporting with screenshots, HTML dumps, and full execution tracing**

A demo GIF showing the UI test running locally (required by assignment):

📌 *Place your GIF here:*  
`docs/demo.gif`

---

#  Project Structure

 qa-twitch-mobile-test
│
├── .github/
│   └── workflows/
│       └── python-app.yml             
│
├── pages/
│   ├── __init__.py
│   ├── twitch_home_page.py             
│   └── twitch_streamer_page.py         
│
├── reports/
│   ├── allure/                          
│   └── allure-report/                
│
├── tests/
│   ├── api/
│   │   └── test_public_apis.py          
│   │
│   └── web/
│       └── test_twitch_search.py        
│
├── utils/
│   └── client.py                        
│
├── conftest.py                          
├── pytest.ini                           
├── generate_allure_png.ps1              
└── README.md                            

---

# UI Test Cases (Required by assignment)

| ID        | Test Case                             | Steps                                              | Expected Result                         | Validation Used                            |
| --------- |---------------------------------------| -------------------------------------------------- | --------------------------------------- | ------------------------------------------ |
| UI-01     | Open Twitch homepage                  | Navigate to `https://twitch.tv`                    | Homepage loads fully                    | DOM ready state                            |
| UI-02     | Close cookies                         | Detect & click **Accept Cookies** button           | Cookies modal disappears                | Element visibility + clickability          |
| UI-03     | Open search bar                       | Click search icon                                  | Search input becomes visible            | Element visibility                         |
| UI-04     | Enter search query "StarCraft II"     | Type `"StarCraft II"` into search field and submit | Search results for StarCraft II appear  | Input value assertion + URL contains query |
| UI-05     | Scroll down 2 times                   | Execute JS scroll actions                          | Additional streamers load               | JS scroll + DOM diff                       |
| UI-06     | Select streamer                       | Click first streamer in results                    | Successfully navigates to streamer page | URL change + click success                 |
| UI-07     | Wait for streamer to load             | Wait for video container to appear                 | Player becomes visible                  | Presence of player element                 |
| UI-08     | Play for ~5 seconds                   | Allow Twitch player to run for 5s                  | Stream is stable and playing            | Player element remains stable              |
| UI-09     | Take Screenshot                       | Capture viewport                                   | PNG saved under `/reports/screenshots`  | File existence validation                  |

---

# API Test Cases (Required by assignment)

| ID | API | Description | Validation |
|----|-----|-------------|------------|
| API-01 | Dog API | GET all breeds | status=200, response JSON has dictionary |
| API-02 | Dog API | GET random image | "message" contains valid URL |
| API-03 | Agify | Predict age | JSON has fields: name, age, count |
| API-04 | ReqRes | Create user | status=201, ID + timestamp returned |
| API-05 | Pokémon API | Get Pokémon | Validate name + array of types |

---

#  Validation Logic Explanation

### ✔Why these validations?

The assignment requires:

1. Meaningful validation  
2. Coverage of correctness  
3. Resilience to dynamic data  

### UI Validation:

- **DOM readiness** ensures page fully loads  
- **Cookie modal detection** handles EU GDPR variations  
- **Search validation** confirms successful navigation  
- **Scroll validation** ensures mobile-like behavior  
- **Streamer selection** uses multiple fallback locators  
- **Video player detection** avoids empty screenshots  
- **Final screenshot** acts as proof of correct execution  

### API Validation:

- Validate **status codes**  
- Validate **schema correctness**  
- Validate **response content**  
- Use **retry logic** for flaky public services  

This satisfies the assignment requirement:

> “Provide a description of what validation was used and why.”

---

# Running Tests

### Install dependencies
