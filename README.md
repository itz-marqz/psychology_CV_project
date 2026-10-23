# 🌿 Telegram Booking Assistant & CV Portfolio Website

A fully responsive single-page CV website and an automated Telegram bot built to handle counseling requests, service inquiries, and client information for a professional psychologist. 

Designed with a clean, warm pastel aesthetic, robust security (no plaintext payment details), and an efficient 3-step booking funnel.

---

## 🚀 Features

### 🌐 Website (`index.html`)
* **Warm Pastel Aesthetic:** Styled using custom color accents, soft rounded corners, and professional typography (`Literata` and `Nunito`).
* **Interactive Components:** 
  * JS-powered certificate carousel with swipe support, navigation arrows, and thumbnail zooming.
  * Multi-group expandable contract/informed consent accordion with a direct PDF download link.
* **Privacy-First:** Public payment details (cards, PayPal) were intentionally removed from public views and replaced with an automated instruction flow after booking confirmation.

### 🤖 Telegram Bot (`bot.py`)
* **Interactive FSM (Finite State Machine):** A seamless 3-step booking funnel guiding users from choosing a format (Individual/Package) to sharing their preferred schedule and communication format (Online/Offline in Kyiv).
* **Instant Admin Notifications:** Automatically forwards structured client requests directly to a designated admin chat.
* **Smart Content Delivery:** Handles long legal contracts by splitting them into sequential messages to bypass Telegram character limits.
* **Inline Navigation:** Clean grid-based menu layout for fast navigation (`/start`, services, pricing, terms, and social links).

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3 (Tailwind-inspired styling), Vanilla JavaScript.
* **Backend:** Python 3.10+, `aiogram v3` (modern asynchronous Telegram bot framework).
* **Hosting & Deployment:** Hosted via cloud platforms (configured with `Dockerfile` and environment variables for secure production environments).

---

## 🧩 Challenges & Solutions

Developing and deploying this project came with a few architectural and hosting hurdles:

1. **Cloud Hosting Limitations & Free Tier Restrictions:**
   * *Problem:* Standard free tiers on platforms like Render either put applications to sleep after inactivity or restricted background worker deployments without a paid subscription.
   * *Solution:* Adapted the project infrastructure using containerization (`Dockerfile`) and migrated to flexible continuous-deployment platforms (such as Pella), implementing proper environment variable handling for secure token management.
2. **Telegram Message Length Limits:**
   * *Problem:* The legal contract text exceeded Telegram's single-message character limit, causing formatting crashes when requested via the bot menu.
   * *Solution:* Implemented automated text chunking logic in Python to split the legal agreement into logical, sequential messages without breaking readability.
3. **Public Data Security:**
   * *Problem:* Original reference materials contained sensitive financial data (credit card numbers and direct payment handles) exposed publicly.
   * *Solution:* Refactored both the web interface and bot flows to hide direct financial credentials, routing payment details strictly through secure, verified follow-ups after session approval.

---

## ⚙️ Local Setup & Installation

If you want to run or test the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
   cd your-repo-name
