import React, { useEffect, useState } from "react";
import "../styles/DeadlineCountdown.css";

export default function DeadlineCountdown({ deadlineInfo }) {
  const [countdown, setCountdown] = useState(deadlineInfo);

  useEffect(() => {
    if (!deadlineInfo || !deadlineInfo.deadline) return;

    const update = () => {
      const deadline = new Date(deadlineInfo.deadline);
      const now = new Date();
      const diffMs = deadline - now;
      const isPast = diffMs < 0;
      const abs = Math.abs(diffMs);
      const days = Math.floor(abs / 86400000);
      const hours = Math.floor((abs % 86400000) / 3600000);
      const minutes = Math.floor((abs % 3600000) / 60000);
      const seconds = Math.floor((abs % 60000) / 1000);

      setCountdown({
        ...deadlineInfo,
        is_past_due: isPast,
        days,
        hours,
        minutes,
        seconds,
        human_readable: `${isPast ? "Overdue by" : "Due in"} ${days}d ${hours}h ${minutes}m`,
      });
    };

    update();
    const timer = setInterval(update, 60000);
    return () => clearInterval(timer);
  }, [deadlineInfo]);

  if (!countdown || !countdown.deadline) return null;

  const { is_past_due, days, hours, minutes } = countdown;

  const urgencyClass = is_past_due
    ? "deadline-overdue"
    : days === 0 && hours < 6
    ? "deadline-urgent"
    : days === 0
    ? "deadline-soon"
    : "deadline-normal";

  return (
    <div className={`deadline-countdown ${urgencyClass}`}>
      <span className="deadline-icon">{is_past_due ? "⏰" : "⌛"}</span>
      <span className="deadline-text">
        {is_past_due ? "Overdue" : "Due in"}{" "}
        {days > 0 && `${days}d `}
        {hours}h {minutes}m
      </span>
    </div>
  );
}
