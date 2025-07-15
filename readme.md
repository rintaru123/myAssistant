# My Assistant - A Compact Desktop Helper

A sleek, modern desktop assistant that lives on the edge of your screen, providing quick access to your tasks and notes. Features a unique, immersive "Zen Mode" for focused writing.

This project was born from a fantastic collaboration between a dedicated user and Google's AI assistant, evolving from a simple idea into a feature-rich, polished application.

---
![Blank project](https://github.com/rintaru123/myAssistant/blob/main/screenshots/%D0%9F%D1%83%D1%81%D1%82%D0%BE%D0%B9%20%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82.png)

![Project with some data](https://github.com/rintaru123/myAssistant/blob/main/screenshots/%D0%97%D0%B0%D0%BF%D0%BE%D0%BB%D0%BD%D0%B5%D0%BD%D0%BD%D1%8B%D0%B9%20%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82.png)

![Zen mode](https://github.com/rintaru123/myAssistant/blob/main/screenshots/Zen%20mode.png)

![Settings](https://github.com/rintaru123/myAssistant/blob/main/screenshots/Settings.png)

![About](https://github.com/rintaru123/myAssistant/blob/main/screenshots/%D0%9E%20%D0%BF%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B5.png)

---

## ✨ Features

*   **Slide-Out Interface:** Access your tasks and notes instantly from a trigger button on the edge of your screen.
*   **Task Management:**
    *   Quickly add, delete, and edit tasks.
    *   **Multiple Task Lists:** Organize tasks into different lists (e.g., "Work," "Personal") and easily switch between them.
    *   Mark tasks as complete with a satisfying circular, theme-aware checkbox.
    *   Hide completed tasks to keep your list clean.
*   **Note Taking:**
    *   A powerful notes panel for all your ideas.
    *   **Tagging System:** Organize your notes with hashtags (e.g., `#project`, `#ideas`) and filter by them.
    *   Full-text search to find any note instantly.
*   **Zen Mode:**
    *   An immersive, distraction-free writing environment that hides all other UI.
    *   **Built-in Pomodoro Timer:** Stay focused with a configurable work/break timer.
    *   **Ambient Audio Player** with playlist and single-track support.
    *   Live word count.
    *   Fully customizable background, theme, and fonts.
*   **Deep Customization:**
    *   Choose between **light** and **dark** themes for the entire application.
    *   Set a custom **accent color** that affects buttons and UI elements.
    *   **Fine-grained Theme Control:** Customize the exact background and text colors for both light and dark modes.
    *   Position the trigger button on the **left or right** side of the screen.
*   **Data Safety:**
    *   **Automatic Backups:** Creates a backup of your data every 10 minutes.
    *   **Restore Function:** Easily restore your data from the last backup via the context menu.
    *   **Markdown Export:** Export all your notes into a single, clean `.md` file.

## 🚀 Setup & Installation

This application is built with Python and PyQt6.

1.  **Install Dependencies:**
    Make sure you have Python 3 installed. Then, install the required library:
    ```bash
    pip install PyQt6
    ```

2.  **(Optional) Add Audio Files:**
    Create a folder named `zen_audio` in the same directory as the script. Place any `.mp3` or `.wav` files inside it to use them in the Zen Mode audio player.

3.  **(Optional) Add Pomodoro Sound:**
    Place a short sound file named `pomodoro_end.wav` in the same directory as the script. This sound will play when a Pomodoro session ends.

4.  **Run the Application:**
    ```bash
    python your_script_name.py
    ```

## 📜 License

The source code of this project is licensed under the **MIT License**.

This program uses the **PyQt6** framework, which is licensed under the **GNU General Public License v3 (GPLv3)**. This means that if you distribute this application (or a modified version of it), you must also make the source code available under a GPL-compatible license.

## 🙏 Acknowledgements

This project was brought to life through a wonderful collaboration between a dedicated user with a keen eye for detail and Google's AI assistant. Every feature, bug fix, and UI polish is the result of our joint effort. Thank you for this incredible journey!