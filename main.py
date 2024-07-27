import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QDateTimeEdit, QCalendarWidget,
    QTimeEdit, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QListWidget, QMessageBox,
    QComboBox, QListWidgetItem, QInputDialog
)
from PyQt5.QtCore import QTimer, QDateTime, QThread, pyqtSignal, QDate, QTime  # Added QTime here
from PyQt5.QtGui import QColor, QFont

class NotificationThread(QThread):
    notification_signal = pyqtSignal(str, str)  # Pass title and description

    def run(self):
        while True:
            now = QDateTime.currentDateTime()
            with open('reminders.json', 'r') as f:
                reminders = json.load(f)
            
            for reminder in reminders:
                reminder_time = QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP')
                if reminder_time <= now:
                    self.notification_signal.emit(reminder['title'], reminder['description'])
                    if reminder['recurring'] != 'None':
                        self.scheduleRecurringReminder(reminder)
                    reminders.remove(reminder)
                    with open('reminders.json', 'w') as f:
                        json.dump(reminders, f)
                    break
            QThread.msleep(10000)  # Check every 10 seconds

    def scheduleRecurringReminder(self, reminder):
        if reminder['recurring'] == 'Daily':
            next_time = QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP').addDays(1)
        elif reminder['recurring'] == 'Weekly':
            next_time = QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP').addDays(7)
        elif reminder['recurring'] == 'Monthly':
            next_time = QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP').addMonths(1)
        else:
            return
        
        reminder['time'] = next_time.toString('MM/dd/yyyy hh:mm:ss AP')
        with open('reminders.json', 'r') as f:
            reminders = json.load(f)
        reminders.append(reminder)
        with open('reminders.json', 'w') as f:
            json.dump(reminders, f)

class TaskReminderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.reminders = []
        self.loadReminders()

        self.notification_thread = NotificationThread()
        self.notification_thread.notification_signal.connect(self.showNotification)
        self.notification_thread.start()

    def initUI(self):
        self.setWindowTitle('Task Management Tool')
        self.setGeometry(100, 100, 800, 600)  # Set window size to 800x600 pixels
        
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        
        self.mainLayout = QHBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        
        # Task Input Section (Left Portion)
        self.inputLayout = QVBoxLayout()
        self.inputLayout.setSpacing(10)
        self.inputLayout.setContentsMargins(20, 20, 20, 20)
        
        self.titleLabel = QLabel('Enter Task Title (Max 100 Characters):')
        self.inputLayout.addWidget(self.titleLabel)
        
        self.titleInput = QTextEdit(self)
        self.titleInput.setPlaceholderText('Enter task title')
        self.titleInput.setMaximumHeight(40)  # Height for title input
        self.inputLayout.addWidget(self.titleInput)
        
        self.descriptionLabel = QLabel('Enter Task Description (Max 5000 Characters):')
        self.inputLayout.addWidget(self.descriptionLabel)
        
        self.descriptionInput = QTextEdit(self)
        self.descriptionInput.setPlaceholderText('Enter task description')
        self.descriptionInput.setMaximumHeight(150)  # Height for description input
        self.inputLayout.addWidget(self.descriptionInput)
        
        # Date and Time Selection
        self.dateLabel = QLabel('Select Date:')
        self.inputLayout.addWidget(self.dateLabel)
        
        self.datePicker = QCalendarWidget(self)
        self.datePicker.setMaximumHeight(200)  # Adjust size as needed
        self.inputLayout.addWidget(self.datePicker)
        
        self.timeLabel = QLabel('Select Time:')
        self.inputLayout.addWidget(self.timeLabel)
        
        self.timePicker = QTimeEdit(self)
        self.inputLayout.addWidget(self.timePicker)
        
        self.recurringComboBox = QComboBox(self)
        self.recurringComboBox.addItems(['None', 'Daily', 'Weekly', 'Monthly'])
        self.inputLayout.addWidget(self.recurringComboBox)
        
        self.addButton = QPushButton('Add Task', self)
        self.addButton.clicked.connect(self.addReminder)
        self.inputLayout.addWidget(self.addButton)
        
        self.clearButton = QPushButton('Clear Fields', self)
        self.clearButton.clicked.connect(self.clearFields)
        self.inputLayout.addWidget(self.clearButton)
        
        self.mainLayout.addLayout(self.inputLayout, stretch=1)
        
        # Task Display Section (Right Portion)
        self.taskDisplayLayout = QVBoxLayout()
        self.taskDisplayLayout.setSpacing(10)
        self.taskDisplayLayout.setContentsMargins(20, 20, 20, 20)
        
        self.taskListLabel = QLabel('Task List')
        self.taskDisplayLayout.addWidget(self.taskListLabel)
        
        self.reminderList = QListWidget(self)
        self.reminderList.setStyleSheet("border: 1px solid black;")  # Adding border to the list widget
        self.reminderList.setSpacing(10)  # Add spacing between items
        self.taskDisplayLayout.addWidget(self.reminderList)
        
        self.deleteButton = QPushButton('Delete Reminder', self)
        self.deleteButton.clicked.connect(self.deleteReminder)
        self.taskDisplayLayout.addWidget(self.deleteButton)
        
        self.editButton = QPushButton('Edit Reminder', self)
        self.editButton.clicked.connect(self.editReminder)
        self.taskDisplayLayout.addWidget(self.editButton)
        
        self.snoozeButton = QPushButton('Snooze Reminder', self)
        self.snoozeButton.clicked.connect(self.snoozeReminder)
        self.taskDisplayLayout.addWidget(self.snoozeButton)
        
        self.mainLayout.addLayout(self.taskDisplayLayout, stretch=1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.checkReminders)
        self.timer.start(10000)  # Check every 10 seconds

    def addReminder(self):
        title = self.titleInput.toPlainText()
        description = self.descriptionInput.toPlainText()
        date = self.datePicker.selectedDate().toString('MM/dd/yyyy')
        time = self.timePicker.time().toString('hh:mm:ss AP')
        reminder_time = f"{date} {time}"
        recurring = self.recurringComboBox.currentText()

        if not title or not description:
            QMessageBox.warning(self, 'Input Error', 'Task title and description cannot be empty.')
            return
        
        if QDateTime.fromString(reminder_time, 'MM/dd/yyyy hh:mm:ss AP') <= QDateTime.currentDateTime():
            QMessageBox.warning(self, 'Input Error', 'Reminder time must be in the future.')
            return
        
        reminder = {
            'title': title,
            'description': description,
            'time': reminder_time,
            'recurring': recurring
        }
        self.reminders = [reminder]  # Ensure only one reminder is shown
        self.saveReminders()
        self.updateReminderList()
        self.clearFields()

    def clearFields(self):
        self.titleInput.clear()
        self.descriptionInput.clear()
        self.datePicker.setSelectedDate(QDate.currentDate())
        self.timePicker.setTime(QTime.currentTime())  # Use QTime here
        self.recurringComboBox.setCurrentIndex(0)

    def deleteReminder(self):
        selected_item = self.reminderList.currentItem()
        if selected_item:
            self.reminders = []  # Clear the reminder list
            self.saveReminders()
            self.updateReminderList()
        else:
            QMessageBox.warning(self, 'Selection Error', 'Please select a reminder to delete.')

    def editReminder(self):
        selected_item = self.reminderList.currentItem()
        if selected_item:
            reminder = self.reminders[0] if self.reminders else None

            if reminder:
                title, ok = QInputDialog.getText(self, 'Edit Reminder', 'Enter new title:', text=reminder['title'])
                if ok:
                    description, ok = QInputDialog.getText(self, 'Edit Reminder', 'Enter new description:', text=reminder['description'])
                    if ok:
                        date, ok = QInputDialog.getText(self, 'Edit Reminder', 'Enter new date (MM/dd/yyyy):', text=QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP').toString('MM/dd/yyyy'))
                        if ok:
                            time, ok = QInputDialog.getText(self, 'Edit Reminder', 'Enter new time (hh:mm:ss AP):', text=QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP').toString('hh:mm:ss AP'))
                            if ok:
                                reminder['title'] = title
                                reminder['description'] = description
                                reminder['time'] = f"{date} {time}"
                                self.saveReminders()
                                self.updateReminderList()

    def snoozeReminder(self):
        if self.reminders:
            reminder = self.reminders[0]
            snooze_time = QDateTime.currentDateTime().addMinutes(10).toString('MM/dd/yyyy hh:mm:ss AP')
            reminder['time'] = snooze_time
            self.saveReminders()
            self.updateReminderList()
        else:
            QMessageBox.warning(self, 'Selection Error', 'Please select a reminder to snooze.')

    def showNotification(self, title, description):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Reminder')
        msg_box.setText(f"<b><u><font size='36'>{title}</font></u></b><br><font size='24'>{description}</font>")
        msg_box.exec_()

    def loadReminders(self):
        try:
            with open('reminders.json', 'r') as f:
                self.reminders = json.load(f)
        except FileNotFoundError:
            self.reminders = []

    def saveReminders(self):
        with open('reminders.json', 'w') as f:
            json.dump(self.reminders, f)

    def updateReminderList(self):
        self.reminderList.clear()
        if self.reminders:
            reminder = self.reminders[0]
            item = QListWidgetItem()
            item.setText(f"Title: {reminder['title']}\nDescription: {reminder['description']}\nTime: {reminder['time']}")
            item.setBackground(QColor('transparent'))  # No color for newly added reminders
            self.reminderList.addItem(item)

    def checkReminders(self):
        now = QDateTime.currentDateTime()
        if self.reminders:
            reminder = self.reminders[0]
            reminder_time = QDateTime.fromString(reminder['time'], 'MM/dd/yyyy hh:mm:ss AP')
            if reminder_time <= now:
                self.showNotification(reminder['title'], reminder['description'])
                if reminder['recurring'] != 'None':
                    self.notification_thread.scheduleRecurringReminder(reminder)
                self.reminders = []  # Clear the reminders list after showing the notification
                self.saveReminders()
                self.updateReminderList()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TaskReminderApp()
    ex.show()
    sys.exit(app.exec_())
