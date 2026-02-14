# ⏱️ TimeTracker

A simple, multiplatform time tracking application built with [Flet](https://flet.dev/). Designed for a single user tracking time on their local machine.

![Platform Support](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20iOS%20%7C%20Android%20%7C%20Web-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- **📁 Project Management** - Create, edit, and delete projects to organize your work
- **⏰ Time Tracking** - Log time entries with date, hours, and description
- **📊 Simple Dashboarding** - Keep track of time spent on each project with total hours
- **📥 Excel Export** - Export your time data for use in Excel spreadsheets
- **🎨 Themes** - Light and dark mode support
- **🌐 Multiplatform** - Runs on Windows, macOS, Linux, iOS, Android, and Web

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Run the App

**Desktop App:**
```bash
uv run flet run
```

**Web App:**
```bash
uv run flet run --web
```

## 📦 Building

Build for your target platform:

### Android
```bash
flet build apk -v
```

### iOS
```bash
flet build ipa -v
```

### macOS
```bash
flet build macos -v
```

### Linux
```bash
flet build linux -v
```

### Windows
```bash
flet build windows -v
```

For more details on building and signing, refer to the [Flet Packaging Guide](https://docs.flet.dev/publish/).

## 🛠️ Tech Stack

- **Framework**: [Flet](https://flet.dev/) - Cross-platform UI framework
- **Database**: SQLite - Local data storage
- **Data Processing**: [Polars](https://www.pola.rs/) - Fast DataFrame library
- **Excel Export**: [xlsxwriter](https://xlsxwriter.readthedocs.io/) - Python Excel writer

## 🤝 Contributing

Pull requests are welcome! If you'd like to contribute, feel free to fork the repository and submit a PR.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with love by Luigi.** 

*This tool is provided AS-IS, without warranty of any kind. Use at your own risk.*
