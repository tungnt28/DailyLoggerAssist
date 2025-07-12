# DailyLoggerAssist: AI-Powered Work Tracking & JIRA Automation

![DailyLoggerAssist](https://img.shields.io/badge/DailyLoggerAssist-Ready%20to%20Use-brightgreen)  
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue)](https://github.com/tungnt28/DailyLoggerAssist/releases)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Integrations](#integrations)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

DailyLoggerAssist is an intelligent daily work tracking system designed to enhance productivity through AI-powered automation. This tool integrates seamlessly with JIRA, allowing users to streamline their work processes. Built on FastAPI, Celery, and Redis, it provides a robust backend that ensures quick and efficient task management.

For the latest releases, check out our [Releases section](https://github.com/tungnt28/DailyLoggerAssist/releases). Download and execute the necessary files to get started.

---

## Features

- **AI-Powered Automation**: Automate repetitive tasks and enhance efficiency.
- **JIRA Integration**: Directly connect with JIRA to manage your tasks.
- **FastAPI Backend**: Enjoy a fast and responsive API for your applications.
- **Celery Task Queue**: Handle background tasks efficiently with Celery.
- **Redis Caching**: Speed up your application with Redis caching.
- **Teams/Email Notifications**: Get real-time updates through Microsoft Teams or email.

---

## Technologies Used

- **Python**: The core programming language for development.
- **FastAPI**: A modern web framework for building APIs.
- **Celery**: An asynchronous task queue for handling background tasks.
- **Redis**: An in-memory data structure store for caching.
- **JIRA**: A tool for issue tracking and project management.
- **Microsoft Teams**: A collaboration platform for team communication.
- **Email Services**: For sending notifications and updates.

---

## Installation

To install DailyLoggerAssist, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/tungnt28/DailyLoggerAssist.git
   cd DailyLoggerAssist
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   Create a `.env` file in the root directory and add your configuration:

   ```env
   JIRA_URL=https://your-jira-instance.atlassian.net
   JIRA_USER=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   REDIS_URL=redis://localhost:6379/0
   ```

5. Start the FastAPI server:

   ```bash
   uvicorn main:app --reload
   ```

6. Run Celery worker:

   ```bash
   celery -A worker.celery worker --loglevel=info
   ```

For the latest releases, visit our [Releases section](https://github.com/tungnt28/DailyLoggerAssist/releases) to download and execute the necessary files.

---

## Usage

Once installed, you can start using DailyLoggerAssist:

1. **Access the API**: Open your browser and go to `http://localhost:8000/docs` to view the API documentation.
  
2. **Create a new task**: Use the API to create tasks and assign them to JIRA.

3. **Automate workflows**: Set up automation rules to manage tasks efficiently.

4. **Receive notifications**: Configure Teams or email notifications for task updates.

---

## Integrations

DailyLoggerAssist supports various integrations to enhance your workflow:

- **JIRA**: Manage your projects directly from the tool.
- **Microsoft Teams**: Get notifications and updates in your team chat.
- **Email**: Receive updates and alerts through your email.

### Setting Up Integrations

1. **JIRA**: Follow the [JIRA API documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/) for setup instructions.

2. **Microsoft Teams**: Use the Microsoft Teams API to create a bot for notifications.

3. **Email**: Configure SMTP settings in your `.env` file to enable email notifications.

---

## Contributing

We welcome contributions to DailyLoggerAssist! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

Please ensure your code follows our coding standards and includes appropriate tests.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or feedback, please reach out:

- **Email**: your-email@example.com
- **GitHub**: [tungnt28](https://github.com/tungnt28)

For the latest releases, check out our [Releases section](https://github.com/tungnt28/DailyLoggerAssist/releases). Download and execute the necessary files to get started.