from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255)
    rno = models.CharField(max_length=20)
    stream = models.CharField(max_length=255)
    std = models.CharField(max_length=10)
    encoding = models.TextField()
    status = models.CharField(max_length=1, default='A')

    def __str__(self):
        return self.name
    
    # Add a FileField for the Excel file
    excel_file = models.FileField(upload_to='excel_files/', null=True, blank=True)