from django.db.models.signals import post_save
from django.dispatch import receiver
import pandas as pd
import os

from .models import Student

@receiver(post_save, sender=Student)
def generate_excel_file(sender, instance, **kwargs):
    if not instance.excel_file:
        # Generate Excel file
        data = {
            'Name': [instance.name],
            'Roll Number': [instance.rno],
            'Stream': [instance.stream],
            'Standard': [instance.std],
            'Status': [instance.status],
        }
        df = pd.DataFrame(data)

        # Specify the file path
        excel_folder = os.path.join('media', 'excel_files')
        os.makedirs(excel_folder, exist_ok=True)

        excel_file_path = os.path.join(excel_folder, f'attendance_{instance.stream}_{instance.std}.xlsx')
        df.to_excel(excel_file_path, index=False)

        # Save the file path to the instance
        instance.excel_file = f'excel_files/attendance_{instance.stream}_{instance.std}.xlsx'
        instance.save()