# Streamlit Call Analytics Dashboard

A real-time, interactive dashboard built using **Streamlit** to analyze and visualize call activity metrics from the GoTo API. This tool is designed to support internal healthcare operations by monitoring call behavior, detecting performance patterns, and assisting with workforce accountability.

---

## GoTo API Access Token Setup

This dashboard integrates directly with the GoTo Call History API. To retrieve data, the OAuth2 Authorization Code Flow is used.

### Manual Token Generation via Postman:

1. **Register** an app on the [GoTo Developer Portal](https://developer.goto.com/)
2. **Configure OAuth2 Authorization** in Postman:
   - Authorization Type: OAuth 2.0
   - Authorization URL: `https://authentication.logmeininc.com/oauth/authorize`
   - Token URL: `https://authentication.logmeininc.com/oauth/token`
   - Callback URL: `https://oauth.pstmn.io/v1/callback`
   - Set required fields: `scope`, `client_id`, and `client_secret`
3. **Authorize manually** by logging into your GoTo developer account when prompted.
4. **Copy the `access_token`** from the Postman response for use in the dashboard.

> Note: GoTo's OAuth2 flow requires multiple steps and careful coordination between account keys and user tokens. The lack of fully documented examples made the process more challenging than typical API integrations.

For help replicating this setup or accessing the token securely, feel free to reach out directly.

**Contact:**
- Email: [yannamsatyateja@gmail.com](mailto:yannamsatyateja@gmail.com)
- GitHub: [github.com/satyayannam](https://github.com/satyayannam)
- LinkedIn: [linkedin.com/in/satyayannam](https://linkedin.com/in/satyayannam)

---

## Features

- Aggregates call activity including total and missed calls
- User-specific call duration and activity analysis
- Time-gap analysis to identify potential performance issues
- Date-based filtering and pagination support
- Real-time visualization through Streamlit interface
- Integration with OAuth2-secured GoTo API endpoints

---

## Dashboard Preview


<img width="1449" height="770" alt="Screenshot 2025-07-11 165353" src="https://github.com/user-attachments/assets/76403933-df76-462d-9d4c-ba11782b045a" />
<img width="1390" height="470" alt="Screenshot 2025-07-12 180512" src="https://github.com/user-attachments/assets/58ff636f-3409-445a-8782-35d197804626" />
<img width="1854" height="791" alt="Screenshot 2025-07-12 181136" src="https://github.com/user-attachments/assets/511e814f-fb58-499e-bbc8-cba2a4c7bf39" />
<img width="1429" height="813" alt="Screenshot 2025-07-12 180553" src="https://github.com/user-attachments/assets/0b932e53-55d9-41ca-9d2a-708a9f310264" />
<img width="1379" height="672" alt="Screenshot 2025-07-12 181200" src="https://github.com/user-attachments/assets/91674d1c-2495-4588-bb59-0722a5c138b8" />

<img width="1395" height="675" alt="Screenshot 2025-07-12 181218" src="https://github.com/user-attachments/assets/c6e7f3d9-85f9-4b62-b4ef-260af8074678" />
---


## Planned Enhancements

- Automate OAuth2 token refresh to eliminate manual intervention
- Export analytics summaries to Google Sheets
- Introduce user-specific filters by department, time of day, or call type
- Add Slack/Email alerting for key thresholds (e.g., missed calls)
- Build historical benchmarking by individual, team, or shift

---

## Project Structure

```bash
├── .streamlit/
│   └── secrets.toml             # Streamlit sharing credentials
├── api/
│   ├── calls.py                 # Handles GoTo API call fetches
│   ├── users.py                 # Retrieves user and account identifiers
│   └── webhook.py               # (Reserved) Live API hook integration
├── logic/
│   ├── flagging.py              # Rules for time gap / performance detection
│   ├── overall.py               # Dashboard logic for aggregate views
│   └── userwise.py              # Dashboard logic for individual users
├── utils/
│   └── processing.py            # Preprocessing and utility functions
├── .env                         # Environment configuration (client_id, secret)
├── .gitignore                   # Excludes sensitive and system files
├── app.py                       # Entry point for Streamlit application
├── config.py                    # Constants and application settings
├── README.md                    # Documentation file
├── requirements.txt             # Python package dependencies
