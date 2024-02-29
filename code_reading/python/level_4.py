class UserModel:
    def __init__(self, name, email, database, email_service):
        self.name = name
        self.email = email
        self.database = database
        self.email_service = email_service

    def set_name(self, new_name):
        if new_name:
            self.name = new_name
        else:
            return Exception("Error: Empty name provided!")

    def get_name(self):
        return self.name

    def save_to_database(self):
        # Assume a database connection is established here
        if len(self.name) > 0:
            self.database.save(self.name)
        else:
            raise Exception("Error: Cannot save empty name to database!")

    def load_from_database(self, name):
        data = self.database.load(name)
        if data:
            self.name = data
        else:
            raise Exception("Error: Data not found in database!")

    def save_to_file(self):
        with open("output.txt", "w") as file:
            file.write(self.name)

    def send_email(self, recipient):
        if recipient:
            self.email_service.send_email(recipient, self.name)
        else:
            Exception("Error: No recipient provided!")

    def validate_name(self):
        if len(self.name) < 3:
            raise Exception("Error: Name must be at least 3 characters long!")
        elif len(self.name) > 50:
            raise Exception("Error: Name cannot exceed 50 characters!")
        elif not self.name.isalpha():
            raise Exception("Error: Name must contain only alphabetic characters!")

    def generate_report(self):
        # Assume a report generation library is imported and configured
        report = ReportGenerator.generate(self.name)
        return report
