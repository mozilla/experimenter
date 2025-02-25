# Generated by Django 5.0.2 on 2024-03-04 16:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("legacy_experiments", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="experiment",
            name="firefox_max_version",
            field=models.CharField(
                blank=True,
                choices=[
                    ("55.0", "Firefox 55.0"),
                    ("56.0", "Firefox 56.0"),
                    ("57.0", "Firefox 57.0"),
                    ("58.0", "Firefox 58.0"),
                    ("59.0", "Firefox 59.0"),
                    ("60.0", "Firefox 60.0"),
                    ("61.0", "Firefox 61.0"),
                    ("62.0", "Firefox 62.0"),
                    ("63.0", "Firefox 63.0"),
                    ("64.0", "Firefox 64.0"),
                    ("65.0", "Firefox 65.0"),
                    ("66.0", "Firefox 66.0"),
                    ("67.0", "Firefox 67.0"),
                    ("68.0", "Firefox 68.0"),
                    ("69.0", "Firefox 69.0"),
                    ("70.0", "Firefox 70.0"),
                    ("71.0", "Firefox 71.0"),
                    ("72.0", "Firefox 72.0"),
                    ("73.0", "Firefox 73.0"),
                    ("74.0", "Firefox 74.0"),
                    ("75.0", "Firefox 75.0"),
                    ("76.0", "Firefox 76.0"),
                    ("77.0", "Firefox 77.0"),
                    ("78.0", "Firefox 78.0"),
                    ("79.0", "Firefox 79.0"),
                    ("80.0", "Firefox 80.0"),
                    ("81.0", "Firefox 81.0"),
                    ("82.0", "Firefox 82.0"),
                    ("83.0", "Firefox 83.0"),
                    ("84.0", "Firefox 84.0"),
                    ("85.0", "Firefox 85.0"),
                    ("86.0", "Firefox 86.0"),
                    ("87.0", "Firefox 87.0"),
                    ("88.0", "Firefox 88.0"),
                    ("89.0", "Firefox 89.0"),
                    ("90.0", "Firefox 90.0"),
                    ("91.0", "Firefox 91.0"),
                    ("92.0", "Firefox 92.0"),
                    ("93.0", "Firefox 93.0"),
                    ("94.0", "Firefox 94.0"),
                    ("95.0", "Firefox 95.0"),
                    ("96.0", "Firefox 96.0"),
                    ("97.0", "Firefox 97.0"),
                    ("98.0", "Firefox 98.0"),
                    ("99.0", "Firefox 99.0"),
                    ("100.0", "Firefox 100.0"),
                    ("101.0", "Firefox 101.0"),
                    ("102.0", "Firefox 102.0"),
                    ("103.0", "Firefox 103.0"),
                    ("104.0", "Firefox 104.0"),
                    ("105.0", "Firefox 105.0"),
                    ("106.0", "Firefox 106.0"),
                    ("107.0", "Firefox 107.0"),
                    ("108.0", "Firefox 108.0"),
                    ("109.0", "Firefox 109.0"),
                    ("110.0", "Firefox 110.0"),
                    ("111.0", "Firefox 111.0"),
                    ("112.0", "Firefox 112.0"),
                    ("113.0", "Firefox 113.0"),
                    ("114.0", "Firefox 114.0"),
                    ("115.0", "Firefox 115.0"),
                    ("116.0", "Firefox 116.0"),
                    ("117.0", "Firefox 117.0"),
                    ("118.0", "Firefox 118.0"),
                    ("119.0", "Firefox 119.0"),
                    ("120.0", "Firefox 120.0"),
                    ("121.0", "Firefox 121.0"),
                    ("122.0", "Firefox 122.0"),
                    ("123.0", "Firefox 123.0"),
                    ("124.0", "Firefox 124.0"),
                    ("125.0", "Firefox 125.0"),
                    ("126.0", "Firefox 126.0"),
                    ("127.0", "Firefox 127.0"),
                    ("128.0", "Firefox 128.0"),
                    ("129.0", "Firefox 129.0"),
                    ("130.0", "Firefox 130.0"),
                    ("131.0", "Firefox 131.0"),
                    ("132.0", "Firefox 132.0"),
                    ("133.0", "Firefox 133.0"),
                    ("134.0", "Firefox 134.0"),
                    ("135.0", "Firefox 135.0"),
                    ("136.0", "Firefox 136.0"),
                    ("137.0", "Firefox 137.0"),
                    ("138.0", "Firefox 138.0"),
                    ("139.0", "Firefox 139.0"),
                    ("140.0", "Firefox 140.0"),
                ],
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="firefox_min_version",
            field=models.CharField(
                blank=True,
                choices=[
                    ("55.0", "Firefox 55.0"),
                    ("56.0", "Firefox 56.0"),
                    ("57.0", "Firefox 57.0"),
                    ("58.0", "Firefox 58.0"),
                    ("59.0", "Firefox 59.0"),
                    ("60.0", "Firefox 60.0"),
                    ("61.0", "Firefox 61.0"),
                    ("62.0", "Firefox 62.0"),
                    ("63.0", "Firefox 63.0"),
                    ("64.0", "Firefox 64.0"),
                    ("65.0", "Firefox 65.0"),
                    ("66.0", "Firefox 66.0"),
                    ("67.0", "Firefox 67.0"),
                    ("68.0", "Firefox 68.0"),
                    ("69.0", "Firefox 69.0"),
                    ("70.0", "Firefox 70.0"),
                    ("71.0", "Firefox 71.0"),
                    ("72.0", "Firefox 72.0"),
                    ("73.0", "Firefox 73.0"),
                    ("74.0", "Firefox 74.0"),
                    ("75.0", "Firefox 75.0"),
                    ("76.0", "Firefox 76.0"),
                    ("77.0", "Firefox 77.0"),
                    ("78.0", "Firefox 78.0"),
                    ("79.0", "Firefox 79.0"),
                    ("80.0", "Firefox 80.0"),
                    ("81.0", "Firefox 81.0"),
                    ("82.0", "Firefox 82.0"),
                    ("83.0", "Firefox 83.0"),
                    ("84.0", "Firefox 84.0"),
                    ("85.0", "Firefox 85.0"),
                    ("86.0", "Firefox 86.0"),
                    ("87.0", "Firefox 87.0"),
                    ("88.0", "Firefox 88.0"),
                    ("89.0", "Firefox 89.0"),
                    ("90.0", "Firefox 90.0"),
                    ("91.0", "Firefox 91.0"),
                    ("92.0", "Firefox 92.0"),
                    ("93.0", "Firefox 93.0"),
                    ("94.0", "Firefox 94.0"),
                    ("95.0", "Firefox 95.0"),
                    ("96.0", "Firefox 96.0"),
                    ("97.0", "Firefox 97.0"),
                    ("98.0", "Firefox 98.0"),
                    ("99.0", "Firefox 99.0"),
                    ("100.0", "Firefox 100.0"),
                    ("101.0", "Firefox 101.0"),
                    ("102.0", "Firefox 102.0"),
                    ("103.0", "Firefox 103.0"),
                    ("104.0", "Firefox 104.0"),
                    ("105.0", "Firefox 105.0"),
                    ("106.0", "Firefox 106.0"),
                    ("107.0", "Firefox 107.0"),
                    ("108.0", "Firefox 108.0"),
                    ("109.0", "Firefox 109.0"),
                    ("110.0", "Firefox 110.0"),
                    ("111.0", "Firefox 111.0"),
                    ("112.0", "Firefox 112.0"),
                    ("113.0", "Firefox 113.0"),
                    ("114.0", "Firefox 114.0"),
                    ("115.0", "Firefox 115.0"),
                    ("116.0", "Firefox 116.0"),
                    ("117.0", "Firefox 117.0"),
                    ("118.0", "Firefox 118.0"),
                    ("119.0", "Firefox 119.0"),
                    ("120.0", "Firefox 120.0"),
                    ("121.0", "Firefox 121.0"),
                    ("122.0", "Firefox 122.0"),
                    ("123.0", "Firefox 123.0"),
                    ("124.0", "Firefox 124.0"),
                    ("125.0", "Firefox 125.0"),
                    ("126.0", "Firefox 126.0"),
                    ("127.0", "Firefox 127.0"),
                    ("128.0", "Firefox 128.0"),
                    ("129.0", "Firefox 129.0"),
                    ("130.0", "Firefox 130.0"),
                    ("131.0", "Firefox 131.0"),
                    ("132.0", "Firefox 132.0"),
                    ("133.0", "Firefox 133.0"),
                    ("134.0", "Firefox 134.0"),
                    ("135.0", "Firefox 135.0"),
                    ("136.0", "Firefox 136.0"),
                    ("137.0", "Firefox 137.0"),
                    ("138.0", "Firefox 138.0"),
                    ("139.0", "Firefox 139.0"),
                    ("140.0", "Firefox 140.0"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
