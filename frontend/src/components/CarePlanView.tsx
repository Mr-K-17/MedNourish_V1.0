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
  Utensils,
  CheckCircle2,
  XCircle,
  Flame,
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

interface NutritionCategoryData {
  title: string;
  regular_foods: string[];
  fruits_to_consume: string[];
  habits_to_improve: string[];
  what_to_eat: string[];
  what_to_avoid: string[];
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

  // Nutrition guide state
  const [nutritionDb, setNutritionDb] = useState<Record<string, NutritionCategoryData>>({});
  const [selectedDeficiency, setSelectedDeficiency] = useState<string>('Vitamin A Deficiency');
  const [addedGoalMessage, setAddedGoalMessage] = useState<string | null>(null);

  // Form state
  const [newTitle, setNewTitle] = useState<string>('');
  const [newCategory, setNewCategory] = useState<'water' | 'food' | 'exercise' | 'sleep' | 'general'>('food');
  const [newReminderTime, setNewReminderTime] = useState<string>('');

  useEffect(() => {
    fetchTasks();
    fetchNutritionGuide();
  }, [idToken]);

  const fetchNutritionGuide = async () => {
    try {
      const res = await fetch('/data/v3_food_nutrition_guide.json');
      if (res.ok) {
        const data = await res.json();
        setNutritionDb(data);
      }
    } catch {
      // Guide loads smoothly
    }
  };

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

  const handleQuickAddFoodGoal = async (goalText: string) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          title: goalText.slice(0, 130),
          category: 'food',
          target_frequency: 'daily',
          reminder_time: '12:30',
        }),
      });
      if (res.ok) {
        setAddedGoalMessage(`Added goal: "${goalText.slice(0, 50)}..."`);
        setTimeout(() => setAddedGoalMessage(null), 3500);
        fetchTasks();
      }
    } catch {
      setErrorMessage('Could not add goal to CarePlan.');
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

  const currentGuide = nutritionDb[selectedDeficiency];

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
          <CalendarCheck size={24} color="var(--color-primary)" />
          <h2 className={styles.title}>CarePlan Wellness Routines & Dietary Guide</h2>
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

      {/* Notice Banner */}
      <div className={styles.noticeBanner}>
        <Info size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Educational Nutrition Guide:</strong>{' '}
          {disclaimer ||
            'CarePlan provides whole-food nutritional suggestions, fruit categories, and lifestyle routines to support dietary wellness. Not a clinical prescription or medication schedule.'}
        </div>
      </div>

      {reminderNotice && (
        <div className={styles.reminderNotice}>
          <Bell size={16} style={{ flexShrink: 0 }} />
          <span>
            <strong>Reminder Notice:</strong> {reminderNotice}
          </span>
        </div>
      )}

      {addedGoalMessage && (
        <div style={{ padding: '0.75rem 1rem', background: '#dcfce7', border: '1px solid #86efac', borderRadius: '8px', color: '#166534', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={18} /> {addedGoalMessage}
        </div>
      )}

      {/* V3 ENHANCED SECTION: RICH DIET & NUTRITION GUIDE */}
      <div
        style={{
          background: 'var(--color-bg-surface)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--color-border)',
          padding: '1.5rem',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'var(--color-primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
              <Utensils size={22} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: 'var(--color-primary-dark)' }}>
                Targeted Food & Diet Optimization Guide
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.825rem', color: 'var(--color-text-secondary)' }}>
                Everyday foods, seasonal fruits, absorption habits, and what to eat vs avoid.
              </p>
            </div>
          </div>

          {/* Deficiency Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="deficiencySelect" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              Select Nutritional Focus:
            </label>
            <select
              id="deficiencySelect"
              value={selectedDeficiency}
              onChange={(e) => setSelectedDeficiency(e.target.value)}
              style={{
                padding: '0.45rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid var(--color-border-strong)',
                background: '#ffffff',
                fontWeight: 600,
                color: 'var(--color-primary-dark)',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {Object.keys(nutritionDb).map((key) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </select>
          </div>
        </div>

        {currentGuide ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
            {/* Card 1: Everyday Foods */}
            <div
              style={{
                background: 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%)',
                border: '1px solid #bbf7d0',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Apple size={18} color="#15803d" />
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#15803d', fontWeight: 700 }}>
                  Everyday Foods People Regularly Eat
                </h4>
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, flex: 1 }}>
                {currentGuide.regular_foods.map((food, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>
                    {food}
                  </li>
                ))}
              </ul>
              <button
                type="button"
                onClick={() => handleQuickAddFoodGoal(`Eat ${currentGuide.regular_foods[0]}`)}
                style={{
                  marginTop: '0.85rem',
                  padding: '0.35rem 0.65rem',
                  background: '#dcfce7',
                  border: '1px solid #86efac',
                  color: '#15803d',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                }}
              >
                <Plus size={13} /> Add top food to CarePlan checklist
              </button>
            </div>

            {/* Card 2: Fruits to Consume */}
            <div
              style={{
                background: 'linear-gradient(135deg, #fff7ed 0%, #ffffff 100%)',
                border: '1px solid #fed7aa',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Flame size={18} color="#c2410c" />
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#c2410c', fontWeight: 700 }}>
                  Fruits Category to Consume
                </h4>
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, flex: 1 }}>
                {currentGuide.fruits_to_consume.map((fruit, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>
                    {fruit}
                  </li>
                ))}
              </ul>
              <button
                type="button"
                onClick={() => handleQuickAddFoodGoal(`Enjoy daily fruit: ${currentGuide.fruits_to_consume[0]}`)}
                style={{
                  marginTop: '0.85rem',
                  padding: '0.35rem 0.65rem',
                  background: '#ffedd5',
                  border: '1px solid #fdba74',
                  color: '#c2410c',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                }}
              >
                <Plus size={13} /> Add fruit goal to CarePlan
              </button>
            </div>

            {/* Card 3: Food Habits to Improve */}
            <div
              style={{
                background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 100%)',
                border: '1px solid #bfdbfe',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Activity size={18} color="#1d4ed8" />
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#1d4ed8', fontWeight: 700 }}>
                  Food Habits to Improve
                </h4>
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, flex: 1 }}>
                {currentGuide.habits_to_improve.map((habit, i) => (
                  <li key={i} style={{ marginBottom: '6px' }}>
                    {habit}
                  </li>
                ))}
              </ul>
            </div>

            {/* Card 4: What to Eat vs What to Avoid */}
            <div
              style={{
                background: '#ffffff',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.85rem',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
                  <CheckCircle2 size={16} color="#16a34a" />
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#16a34a' }}>
                    What to Prioritize (Boosters)
                  </span>
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.8rem', color: '#334155', lineHeight: 1.5 }}>
                  {currentGuide.what_to_eat.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.65rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
                  <XCircle size={16} color="#dc2626" />
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#dc2626' }}>
                    What to Avoid / Limit (Inhibitors)
                  </span>
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.15rem', fontSize: '0.8rem', color: '#64748b', lineHeight: 1.5 }}>
                  {currentGuide.what_to_avoid.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--color-text-muted)' }}>
            Loading nutrition guidance database...
          </div>
        )}
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
          <Plus size={18} color="var(--color-primary)" /> Add a Daily Wellness Habit
        </h3>

        <form onSubmit={handleCreateTask}>
          <div className={styles.formGrid}>
            <div className={styles.inputGroup}>
              <label htmlFor="taskTitle" className={styles.inputLabel}>
                Task Title (e.g. Eat 1 bowl sprouted moong, drink 2.5L water)
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
                <option value="food">Wholesome Nutrition & Food</option>
                <option value="water">Hydration (Water)</option>
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
              Select a nutritional focus above or create your first daily wellness goal to start tracking healthy habits.
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

export default CarePlanView;
