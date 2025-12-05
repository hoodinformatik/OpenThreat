"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Notification, NotificationListResponse } from "@/types/notification";
import { formatDistanceToNow } from "date-fns";
import { Bell, Check, CheckCheck, MessageSquare, ThumbsUp, X, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NotificationsPage() {
  const { token, isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  const fetchNotifications = async () => {
    if (!isAuthenticated || !token) return;

    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/notifications?page=${page}&page_size=${pageSize}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data: NotificationListResponse = await response.json();
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
        setTotal(data.total);
      }
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationIds: number[]) => {
    if (!token) return;

    try {
      const response = await fetch("/api/v1/notifications/mark-read", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ notification_ids: notificationIds }),
      });

      if (response.ok) {
        setNotifications(
          notifications.map((n) =>
            notificationIds.includes(n.id) ? { ...n, is_read: true } : n
          )
        );
        setUnreadCount(Math.max(0, unreadCount - notificationIds.length));
      }
    } catch (error) {
      console.error("Failed to mark notifications as read:", error);
    }
  };

  const markAllAsRead = async () => {
    if (!token) return;

    try {
      const response = await fetch("/api/v1/notifications/mark-all-read", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
        setUnreadCount(0);
      }
    } catch (error) {
      console.error("Failed to mark all as read:", error);
    }
  };

  const deleteNotification = async (notificationId: number) => {
    if (!token) return;

    try {
      const response = await fetch(`/api/v1/notifications/${notificationId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const notification = notifications.find((n) => n.id === notificationId);
        setNotifications(notifications.filter((n) => n.id !== notificationId));
        setTotal(total - 1);
        if (notification && !notification.is_read) {
          setUnreadCount(Math.max(0, unreadCount - 1));
        }
      }
    } catch (error) {
      console.error("Failed to delete notification:", error);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "reply":
        return <MessageSquare className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case "vote_milestone":
        return <ThumbsUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />;
      default:
        return <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getNotificationLink = (notification: Notification) => {
    if (notification.cve_id && notification.comment_id) {
      return `/vulnerabilities/${notification.cve_id}#comment-${notification.comment_id}`;
    }
    if (notification.cve_id) {
      return `/vulnerabilities/${notification.cve_id}`;
    }
    return "#";
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
    }
  }, [isAuthenticated, page]);

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <Bell className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Sign in to view notifications
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You need to be signed in to see your notifications.
          </p>
          <Link
            href="/auth"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Notifications</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {unreadCount > 0
                  ? `${unreadCount} unread notification${unreadCount === 1 ? "" : "s"}`
                  : "All caught up!"}
              </p>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="flex items-center gap-2 px-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
              >
                <CheckCheck className="w-4 h-4" />
                Mark all as read
              </button>
            )}
          </div>
        </div>

        {/* Notifications List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400"></div>
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
              <Bell className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">No notifications yet</p>
              <p className="text-sm">We'll notify you when something happens</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    !notification.is_read ? "bg-blue-50 dark:bg-blue-900/20" : ""
                  }`}
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <Link
                        href={getNotificationLink(notification)}
                        onClick={() => {
                          if (!notification.is_read) {
                            markAsRead([notification.id]);
                          }
                        }}
                        className="block"
                      >
                        <p className="text-base font-medium text-gray-900 dark:text-white">
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                          {formatDistanceToNow(new Date(notification.created_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </Link>
                    </div>

                    {/* Actions */}
                    <div className="flex-shrink-0 flex items-center gap-2">
                      {!notification.is_read && (
                        <button
                          onClick={() => markAsRead([notification.id])}
                          className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                          title="Mark as read"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, total)} of {total} notifications
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page >= Math.ceil(total / pageSize)}
                  className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
