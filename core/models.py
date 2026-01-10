from django.db import models


class AppUser(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    nickname = models.CharField(max_length=64)
    school = models.CharField(max_length=128, blank=True, null=True)
    tags = models.CharField(max_length=256, blank=True, null=True)
    credit_score = models.IntegerField(default=80)
    points = models.IntegerField(default=20)
    activity_points = models.IntegerField(default=0)
    token = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nickname


class Survey(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    owner = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=500)
    reward_points = models.IntegerField(default=0)
    deadline = models.CharField(max_length=64, blank=True, null=True)
    estimated_minutes = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=32, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class FillRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    duration_seconds = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=32, default="pending")
    points_awarded = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class PointsLog(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    delta = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    reporter = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    target_type = models.CharField(max_length=32)
    target_id = models.CharField(max_length=64)
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=32, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
