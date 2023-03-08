from django.test import TestCase

from experimenter.legacy.notifications.tests.factories import NotificationFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNotificationModel(TestCase):
    def test_has_unread_false_when_all_read(self):
        user = UserFactory.create()

        for i in range(3):
            NotificationFactory.create(user=user, read=True)

        self.assertFalse(user.notifications.has_unread)

    def test_has_unread_true_when_some_unread(self):
        user = UserFactory.create()

        NotificationFactory.create(user=user, read=False)

        self.assertTrue(user.notifications.has_unread)

    def test_get_unread_returns_unread_and_marks_as_read(self):
        user = UserFactory.create()

        unread_notifications = []
        for i in range(3):
            unread_notifications.append(NotificationFactory.create(user=user, read=False))

        read_notifications = []
        for i in range(3):
            read_notifications.append(NotificationFactory.create(user=user, read=True))

        self.assertTrue(user.notifications.has_unread)

        notifications = user.notifications.get_unread()

        self.assertFalse(user.notifications.has_unread)

        self.assertEqual(set(notifications), set(unread_notifications))

    def test_get_unread_returns_notifications_for_one_user(self):
        user1 = UserFactory.create()
        user2 = UserFactory.create()

        user1_notifications = []
        user2_notifications = []
        for i in range(3):
            user1_notifications.append(NotificationFactory.create(user=user1))
            user2_notifications.append(NotificationFactory.create(user=user2))

        self.assertEqual(set(user1.notifications.get_unread()), set(user1_notifications))
        self.assertEqual(set(user1.notifications.get_unread()), set([]))

        self.assertEqual(set(user2.notifications.get_unread()), set(user2_notifications))
        self.assertEqual(set(user2.notifications.get_unread()), set([]))
