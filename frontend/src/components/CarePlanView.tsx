import React, { useState, useEffect } from 'react';
import {
  CalendarCheck,
  ArrowLeft,
  Plus,
  Check,
  Trash2,
  Clock,
  Info,
  Droplets,
  Apple,
  Activity,
  Moon,
  Sparkles,
  Bell,
  Download,
} from 'lucide-react';
import styles from './CarePlanView.module.css';

interface CarePlanTask {
  id: string;
  title: string;
  category: 'water' | 'food' | 'exercise' | 'sleep' | 'general';
  target_frequency?: string;
  reminder_time?: string;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
}

interface CarePlanResponse {
  tasks: CarePlanTask[];
  total_count: number;
  completed_count: number;
  reminder_notice: string;
  disclaimer: string;
}

interface CarePlanViewProps {
  idToken: string;
  onBackToDashboard: () => void;
}

export const CarePlanView: React.FC<CarePlanViewProps> = ({
  idToken,
  onBackToDashboard,
}) => {
  const [tasks, setTasks] = useState<CarePlanTask[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [completedCount, setCompletedCount] = useState<number>(0);
  const [reminderNotice, setReminderNotice] = useState<string>(
    'Reminders only alert while this app is open in your browser.'
  );
  const [disclaimer, setDisclaimer] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form state
  const [newTitle, setNewTitle] = useState<string>('');
  const [newCategory, setNewCategory] = useState<'water' | 'food' | 'exercise' | 'sleep' | 'general'>('water');
  const [newReminderTime, setNewReminderTime] = useState<string>('');

  useEffect(() => {
    fetchTasks();
  }, [idToken]);

  const fetchTasks = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/tasks', {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data: CarePlanResponse = await res.json();
        setTasks(data.tasks);
        setTotalCount(data.total_count);
        setCompletedCount(data.completed_count);
        setReminderNotice(data.reminder_notice);
        setDisclaimer(data.disclaimer);
      } else {
        setErrorMessage('Failed to load CarePlan tasks.');
      }
    } catch {
      setErrorMessage('Backend service unreachable. Check if API server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    // Client-side safety check: reject medication words per C-08, C-22
    const forbiddenPattern = /\b(pill|pills|medication|medicine|dose|dosage|prescription|drug|supplement|tablet|capsule|injection|antibiotic|steroid)\b/i;
    if (forbiddenPattern.test(newTitle)) {
      setErrorMessage(
        'Medication and supplement reminders are strictly prohibited in CarePlan (C-08, C-22). Please only enter general wellness tasks (water, food, exercise, sleep).'
      );
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          title: newTitle.trim(),
          category: newCategory,
          target_frequency: 'daily',
          reminder_time: newReminderTime || null,
        }),
      });

      if (res.status === 201) {
        setNewTitle('');
        setNewReminderTime('');
        fetchTasks();
      } else if (res.status === 422) {
        const errorData = await res.json();
        setErrorMessage(
          errorData.detail?.[0]?.msg ||
            'Task rejected: medication and supplement reminders are prohibited.'
        );
      } else {
        setErrorMessage('Failed to create task. Please try again.');
      }
    } catch {
      setErrorMessage('Unable to connect to CarePlan service.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleComplete = async (task: CarePlanTask) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/careplan/tasks/${task.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          is_completed: !task.is_completed,
        }),
      });

      if (res.ok) {
        // Optimistic local update
        setTasks((prev) =>
          prev.map((t) =>
            t.id === task.id ? { ...t, is_completed: !t.is_completed } : t
          )
        );
        setCompletedCount((prev) => (task.is_completed ? prev - 1 : prev + 1));
      } else {
        fetchTasks();
      }
    } catch {
      setErrorMessage('Error updating task completion.');
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    const confirmed = window.confirm('Delete this wellness task?');
    if (!confirmed) return;

    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/careplan/tasks/${taskId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (res.ok) {
        fetchTasks();
      } else {
        setErrorMessage('Failed to delete task.');
      }
    } catch {
      setErrorMessage('Error connecting to CarePlan service.');
    }
  };

  const handleExportICS = () => {
    if (tasks.length === 0) return;
    const now = new Date();
    const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
    const timeStamp = `${now.getUTCFullYear()}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}T${pad(now.getUTCHours())}${pad(now.getUTCMinutes())}${pad(now.getUTCSeconds())}Z`;

    let icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//MedNourish//CarePlan Wellness Schedule//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
    ];

    tasks.forEach((t) => {
      const createdDate = new Date(t.created_at);
      const dtStart = `${createdDate.getUTCFullYear()}${pad(createdDate.getUTCMonth() + 1)}${pad(createdDate.getUTCDate())}T090000Z`;
      icsContent.push('BEGIN:VEVENT');
      icsContent.push(`UID:careplan-${t.id}@mednourish.local`);
      icsContent.push(`DTSTAMP:${timeStamp}`);
      icsContent.push(`DTSTART:${dtStart}`);
      icsContent.push(`SUMMARY:MedNourish Routine: ${t.title}`);
      icsContent.push(`DESCRIPTION:General wellness routine (${t.category}) via MedNourish. Not a medical prescription or clinical treatment.`);
      icsContent.push('RRULE:FREQ=DAILY');
      icsContent.push('STATUS:CONFIRMED');
      icsContent.push('END:VEVENT');
    });

    icsContent.push('END:VCALENDAR');

    const blob = new Blob([icsContent.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `mednourish_careplan_${now.toISOString().slice(0, 10)}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'water':
        return <Droplets size={16} />;
      case 'food':
        return <Apple size={16} />;
      case 'exercise':
        return <Activity size={16} />;
      case 'sleep':
        return <Moon size={16} />;
      default:
        return <Sparkles size={16} />;
    }
  };

  const getCategoryClass = (category: string) => {
    switch (category) {
      case 'water':
        return styles.categoryWater;
      case 'food':
        return styles.categoryFood;
      case 'exercise':
        return styles.categoryExercise;
      case 'sleep':
        return styles.categorySleep;
      default:
        return styles.categoryGeneral;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.headerBar}>
        <button
          type="button"
          onClick={onBackToDashboard}
          className={styles.backButton}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <div className={styles.titleArea}>
          <CalendarCheck size={22} color="var(--color-primary)" />
          <h2 className={styles.title}>CarePlan Wellness Routines</h2>
        </div>
        <button
          type="button"
          onClick={handleExportICS}
          disabled={tasks.length === 0}
          className={styles.backButton}
          title="Download calendar (.ics) file to import into Google Calendar or Apple Calendar"
          style={{ marginLeft: 'auto' }}
        >
          <Download size={15} /> Export Schedule (.ics)
        </button>
      </div>

      <div className={styles.noticeBanner}>
        <Info size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Educational Prototype Notice:</strong>{' '}
          {disclaimer ||
            'CarePlan tasks are self-directed general wellness routines (hydration, food, exercise, sleep), not clinical treatments or medical prescriptions.'}
        </div>
      </div>

      <div className={styles.reminderNotice}>
        <Bell size={16} style={{ flexShrink: 0 }} />
        <span>
          <strong>Important Note (CARE-04):</strong> {reminderNotice}
        </span>
      </div>

      {/* Stats Overview */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Active Tasks</span>
          <span className={styles.statValue}>{totalCount}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Completed</span>
          <span className={styles.statValue}>{completedCount}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Completion Rate</span>
          <span className={styles.statValue}>
            {totalCount > 0 ? `${Math.round((completedCount / totalCount) * 100)}%` : '0%'}
          </span>
        </div>
      </div>

      {/* Add Task Form */}
      <div className={styles.formCard}>
        <h3 className={styles.formTitle}>
          <Plus size={18} color="var(--color-primary)" /> Add a General Wellness Task
        </h3>

        <form onSubmit={handleCreateTask}>
          <div className={styles.formGrid}>
            <div className={styles.inputGroup}>
              <label htmlFor="taskTitle" className={styles.inputLabel}>
                Task Title (e.g., Drink 2L water, 30m brisk walk)
              </label>
              <input
                id="taskTitle"
                type="text"
                className={styles.inputField}
                placeholder="What wellness routine would you like to maintain?"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                maxLength={140}
                required
              />
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="taskCategory" className={styles.inputLabel}>
                Wellness Area
              </label>
              <select
                id="taskCategory"
                className={styles.inputField}
                value={newCategory}
                onChange={(e) =>
                  setNewCategory(
                    e.target.value as 'water' | 'food' | 'exercise' | 'sleep' | 'general'
                  )
                }
              >
                <option value="water">Hydration (Water)</option>
                <option value="food">Wholesome Nutrition</option>
                <option value="exercise">Physical Activity</option>
                <option value="sleep">Sleep & Rest</option>
                <option value="general">General Wellness</option>
              </select>
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="reminderTime" className={styles.inputLabel}>
                In-App Reminder (HH:MM)
              </label>
              <input
                id="reminderTime"
                type="time"
                className={styles.inputField}
                value={newReminderTime}
                onChange={(e) => setNewReminderTime(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isSubmitting || !newTitle.trim()}
            >
              {isSubmitting ? 'Adding...' : 'Add Task'}
            </button>
          </div>
        </form>

        <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>
          * Medication and supplement reminders are strictly excluded per C-08 and C-22.
        </p>
      </div>

      {errorMessage && (
        <div style={{ color: '#b91c1c', background: '#fee2e2', padding: '0.75rem', borderRadius: '6px', fontSize: '0.9rem' }}>
          {errorMessage}
        </div>
      )}

      {/* Task List */}
      <div className={styles.tasksList}>
        <h3 style={{ fontSize: '1.05rem', margin: '0 0 0.5rem 0', color: 'var(--color-text-primary)' }}>
          Your Daily Checklist
        </h3>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-secondary)' }}>
            Loading CarePlan tasks...
          </div>
        ) : tasks.length === 0 ? (
          <div className={styles.emptyState}>
            <CalendarCheck size={40} />
            <h4 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--color-text-primary)' }}>
              No wellness tasks yet
            </h4>
            <p style={{ margin: 0, fontSize: '0.9rem', maxWidth: '400px' }}>
              Create your first daily wellness goal above (hydration, food, exercise, or sleep) to start tracking your healthy habits.
            </p>
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              className={`${styles.taskItem} ${task.is_completed ? styles.taskCompleted : ''}`}
            >
              <div className={styles.taskMain}>
                <button
                  type="button"
                  className={`${styles.checkboxBtn} ${task.is_completed ? styles.checkboxBtnChecked : ''}`}
                  onClick={() => handleToggleComplete(task)}
                  title={task.is_completed ? 'Mark uncompleted' : 'Mark completed'}
                >
                  {task.is_completed && <Check size={16} />}
                </button>

                <div className={styles.taskDetails}>
                  <p
                    className={`${styles.taskTitle} ${task.is_completed ? styles.taskTitleCompleted : ''}`}
                  >
                    {task.title}
                  </p>
                  <div className={styles.taskMeta}>
                    <span
                      className={`${styles.categoryTag} ${getCategoryClass(task.category)}`}
                    >
                      {getCategoryIcon(task.category)} {task.category}
                    </span>
                    {task.reminder_time && (
                      <span>
                        <Clock size={12} style={{ verticalAlign: 'middle', marginRight: '3px' }} />
                        {task.reminder_time}
                      </span>
                    )}
                    {task.is_completed && task.completed_at && (
                      <span style={{ color: '#166534' }}>
                        Completed {new Date(task.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className={styles.actionsGroup}>
                <button
                  type="button"
                  className={styles.deleteBtn}
                  onClick={() => handleDeleteTask(task.id)}
                  title="Delete task"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
