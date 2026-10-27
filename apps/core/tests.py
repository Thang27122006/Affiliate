from django.test import TestCase, Client
from django.urls import reverse


class CoreAppTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_status_and_content(self):
        """Kiểm tra trang chủ trả về HTTP 200 và render đúng template"""
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "Góc Phụ Kiện")
        self.assertContains(response, "Chuột máy tính")
        self.assertContains(response, "Bàn phím")
        self.assertContains(response, "Giá đỡ laptop")
        self.assertTrue(response.context["db_connected"])

    def test_health_check_endpoint(self):
        """Kiểm tra health check API trả về status healthy và kết nối DB hoạt động"""
        response = self.client.get(reverse("core:health_check"))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "healthy")
        self.assertEqual(json_data["database"], "connected")
        self.assertEqual(json_data["project"], "Góc Phụ Kiện")

    def test_admin_portal_accessible(self):
        """Kiểm tra đường dẫn Django Admin truy cập được"""
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quản trị")
