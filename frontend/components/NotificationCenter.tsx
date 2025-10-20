"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Notification, NotificationListResponse } from "@/types/notification";
import { formatDistanceToNow } from "date-fns";
import { Bell, Check, CheckCheck, MessageSquare, ThumbsUp, AtSign, X } from "lucide-react";
import Link from "next/link";

export function NotificationCenter() {
  const { token, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = async () => {
    if (!isAuthenticated || !token) return;

    try {
      setLoading(true);
      const response = await fetch("/api/v1/notifications?page=1&page_size=20", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data: NotificationListResponse = await response.json();
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
      }
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    if (!isAuthenticated || !token) return;

    try {
      const response = await fetch("/api/v1/notifications/unread-count", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.unread_count);
      } else if (response.status === 403 || response.status === 401) {
        // User not authenticated - silently ignore
        setUnreadCount(0);
      }
    } catch (error) {
      // Silently fail - don't spam console
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
        // Update local state
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
      case "mention":
        return <AtSign className="w-4 h-4 text-blue-600" />;
      case "reply":
        return <MessageSquare className="w-4 h-4 text-green-600" />;
      case "vote_milestone":
        return <ThumbsUp className="w-4 h-4 text-purple-600" />;
      default:
        return <Bell className="w-4 h-4 text-gray-600" />;
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
      fetchUnreadCount();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="relative">
      {/* Bell Icon with Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-600 rounded-full">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          ></div>

          {/* Panel */}
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-[600px] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Notifications
              </h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  <CheckCheck className="w-4 h-4" />
                  Mark all read
                </button>
              )}
            </div>

            {/* Notifications List */}
            <div className="overflow-y-auto flex-1">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                  <Bell className="w-12 h-12 mb-2 opacity-50" />
                  <p>No notifications yet</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-gray-50 transition-colors ${
                        !notification.is_read ? "bg-blue-50" : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
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
                              setIsOpen(false);
                            }}
                            className="block"
                          >
                            <p className="text-sm font-medium text-gray-900">
                              {notification.title}
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
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
                              className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                              title="Mark as read"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
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
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
              <div className="p-3 border-t border-gray-200 text-center">
                <Link
                  href="/notifications"
                  onClick={() => setIsOpen(false)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  View all notifications
                </Link>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
