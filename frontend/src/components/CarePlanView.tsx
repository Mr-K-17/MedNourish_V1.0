import React, { useState, useEffect } from 'react';
import {
  CalendarCheck,
  ArrowLeft,
  Plus,
  Check,
  Trash2,
  Clock,
  Activity,
  Sparkles,
  Download,
  Utensils,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RotateCw,
  AlertCircle,
  Apple,
  Bot,
  Search,
  Camera,
} from 'lucide-react';
import styles from './CarePlanView.module.css';

interface MealOption {
  option_index: number;
  food_id: string;
  name: string;
  prep_note: string;
  covers: string[];
  cuisine: string;
}

interface FruitPick {
  food_id: string;
  name: string;
  note: string;
  covers: string[];
}

interface MealSlotData {
  options: MealOption[];
  fruit_side: FruitPick[];
}

interface DayPlan {
  day_index: number;
  date: string;
  day_name: string;
  nutrient_targets: string[];
  meals: {
    breakfast: MealSlotData;
    lunch: MealSlotData;
    dinner: MealSlotData;
  };
}

interface FocusNutrient {
  id: string;
  name: string;
  pct: number;
  source: string;
}

interface MealLog {
  id: string;
  plan_date: string;
  slot: string;
  option_index: number;
  done: boolean;
  done_at?: string | null;
}

interface MealPlanData {
  plan_id: string;
  user_id: string;
  is_baseline: boolean;
  focus_nutrients: FocusNutrient[];
  preferences: {
    diet_pref: string;
    cuisine: string;
    meal_times: Record<string, string>;
  };
  doctor_note?: string | null;
  days: DayPlan[];
  logs?: MealLog[];
}

interface GuidanceCard {
  nutrient_id: string;
  title: string;
  eat_more: string;
  fruit_picks: string[];
  habits_to_improve: string;
  limit_or_avoid: string;
  source_note: string;
}

interface CarePlanTask {
  id: string;
  title: string;
  category: 'water' | 'food' | 'exercise' | 'sleep' | 'general';
  target_frequency?: string;
  reminder_time?: string;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
  is_auto?: boolean;
}

interface CarePlanViewProps {
  idToken: string;
  onBackToDashboard: () => void;
  onNavigateToView?: (view: string) => void;
}

export const CarePlanView: React.FC<CarePlanViewProps> = ({
  idToken,
  onBackToDashboard,
  onNavigateToView,
}) => {
  // Meal Plan State
  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(null);
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(0);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, number>>({});
  const [mealLogs, setMealLogs] = useState<Record<string, boolean>>({});
  const [dayNutrients, setDayNutrients] = useState<{ covered: string[]; pending: string[]; progress_pct: number }>({
    covered: [],
    pending: [],
    progress_pct: 0,
  });
  const [guidanceCards, setGuidanceCards] = useState<GuidanceCard[]>([]);
  const [expandedAccordion, setExpandedAccordion] = useState<Record<string, boolean>>({});

  // Preferences State
  const [dietPref, setDietPref] = useState<string>('veg');
  const [cuisinePref, setCuisinePref] = useState<string>('indian');
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);

  // Calendar Export State
  const [includeMealReminders, setIncludeMealReminders] = useState<boolean>(true);

  // Tasks State (Exercise, Lifestyle, Manual)
  const [tasks, setTasks] = useState<CarePlanTask[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState<'water' | 'food' | 'exercise' | 'sleep' | 'general'>('general');
  const [newReminderTime, setNewReminderTime] = useState('');
  const [isSubmittingTask, setIsSubmittingTask] = useState(false);
  const [taskErrorMessage, setTaskErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchActiveMealPlan();
    fetchPreferences();
    fetchGuidanceCards();
    fetchTasks();
  }, [idToken]);

  const fetchActiveMealPlan = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/meal-plan', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data: MealPlanData = await res.json();
        setMealPlan(data);
        if (data.preferences) {
          setDietPref(data.preferences.diet_pref || 'veg');
          setCuisinePref(data.preferences.cuisine || 'indian');
        }

        // Parse existing logs
        const logMap: Record<string, boolean> = {};
        const optMap: Record<string, number> = {};
        (data.logs || []).forEach((log) => {
          const key = `${log.plan_date}_${log.slot}`;
          if (log.done) {
            logMap[key] = true;
          }
          optMap[key] = log.option_index;
        });
        setMealLogs(logMap);
        setSelectedOptions(optMap);

        // Fetch nutrient status for first day
        if (data.days && data.days.length > 0) {
          fetchDayNutrients(data.days[0].date);
        }
      }
    } catch (e) {
      console.error('Failed to fetch meal plan', e);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPreferences = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/meal-plan/preferences', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDietPref(data.diet_pref);
        setCuisinePref(data.cuisine);
      }
    } catch (e) {
      console.error('Failed to fetch preferences', e);
    }
  };

  const fetchGuidanceCards = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/nutrition-guidance', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setGuidanceCards(data.cards || []);
        // Expand first card by default
        if (data.cards && data.cards.length > 0) {
          setExpandedAccordion({ [data.cards[0].nutrient_id]: true });
        }
      }
    } catch (e) {
      console.error('Failed to fetch nutrition guidance', e);
    }
  };

  const fetchDayNutrients = async (dateStr: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/careplan/meal-plan/nutrients?date=${dateStr}`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDayNutrients({
          covered: data.covered || [],
          pending: data.pending || [],
          progress_pct: data.progress_pct || 0,
        });
      }
    } catch (e) {
      console.error('Failed to fetch day nutrients', e);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/tasks', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTasks(data.tasks || []);
      }
    } catch (e) {
      console.error('Failed to fetch tasks', e);
    }
  };

  const handleUpdatePreferences = async (newDiet: string, newCuisine: string) => {
    setDietPref(newDiet);
    setCuisinePref(newCuisine);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/meal-plan/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          diet_pref: newDiet,
          cuisine: newCuisine,
        }),
      });
      if (res.ok) {
        fetchActiveMealPlan();
      }
    } catch (e) {
      console.error('Failed to update preferences', e);
    }
  };

  const handleForceRegenerate = async () => {
    setIsRegenerating(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/careplan/meal-plan/generate', {
        method: 'POST',
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMealPlan(data);
        if (data.days && data.days.length > 0) {
          fetchDayNutrients(data.days[selectedDayIndex]?.date || data.days[0].date);
        }
      }
    } catch (e) {
      console.error('Failed to regenerate plan', e);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleSelectOption = (slot: string, optIndex: number) => {
    const currentDay = mealPlan?.days?.[selectedDayIndex];
    if (!currentDay) return;
    const key = `${currentDay.date}_${slot}`;
    setSelectedOptions((prev) => ({ ...prev, [key]: optIndex }));

    // If already eaten, update the log with the new option index
    if (mealLogs[key] && mealPlan) {
      logMealEaten(currentDay.date, slot, optIndex, true);
    }
  };

  const handleToggleEaten = (slot: string) => {
    const currentDay = mealPlan?.days?.[selectedDayIndex];
    if (!currentDay || !mealPlan) return;
    const key = `${currentDay.date}_${slot}`;
    const newDone = !mealLogs[key];
    const optIndex = selectedOptions[key] ?? 0;

    setMealLogs((prev) => ({ ...prev, [key]: newDone }));
    logMealEaten(currentDay.date, slot, optIndex, newDone);
  };

  const logMealEaten = async (dateStr: string, slot: string, optIndex: number, done: boolean) => {
    if (!mealPlan) return;
    try {
      await fetch('http://127.0.0.1:8000/v1/careplan/meal-plan/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          plan_id: mealPlan.plan_id,
          plan_date: dateStr,
          slot: slot,
          option_index: optIndex,
          done: done,
        }),
      });
      fetchDayNutrients(dateStr);
    } catch (e) {
      console.error('Failed to log meal', e);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const forbidden = /\b(pill|pills|medication|medicine|dose|dosage|prescription|drug|supplement|tablet|capsule|injection|antibiotic|steroid)\b/i;
    if (forbidden.test(newTitle)) {
      setTaskErrorMessage('Medications and supplements are strictly prohibited in CarePlan tasks.');
      return;
    }

    setIsSubmittingTask(true);
    setTaskErrorMessage(null);
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
      if (res.ok) {
        setNewTitle('');
        setNewReminderTime('');
        fetchTasks();
      } else {
        const err = await res.json();
        setTaskErrorMessage(err.detail?.[0]?.msg || 'Failed to create task.');
      }
    } catch {
      setTaskErrorMessage('Unable to connect to CarePlan service.');
    } finally {
      setIsSubmittingTask(false);
    }
  };

  const handleToggleTaskComplete = async (task: CarePlanTask) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/careplan/tasks/${task.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ is_completed: !task.is_completed }),
      });
      if (res.ok) {
        setTasks((prev) =>
          prev.map((t) => (t.id === task.id ? { ...t, is_completed: !t.is_completed } : t))
        );
      }
    } catch (e) {
      console.error('Failed to toggle task', e);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('Delete this task?')) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/careplan/tasks/${taskId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error('Failed to delete task', e);
    }
  };

  const handleExportICS = () => {
    const now = new Date();
    const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
    const timeStamp = `${now.getUTCFullYear()}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}T${pad(now.getUTCHours())}${pad(now.getUTCMinutes())}${pad(now.getUTCSeconds())}Z`;

    let icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//MedNourish//CarePlan Schedule//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
    ];

    // Export wellness tasks
    tasks.forEach((t) => {
      const d = new Date(t.created_at);
      const dtStart = `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}T090000Z`;
      icsContent.push('BEGIN:VEVENT');
      icsContent.push(`UID:task-${t.id}@mednourish.local`);
      icsContent.push(`DTSTAMP:${timeStamp}`);
      icsContent.push(`DTSTART:${dtStart}`);
      icsContent.push(`SUMMARY:Wellness: ${t.title}`);
      icsContent.push(`DESCRIPTION:General wellness routine via MedNourish.`);
      icsContent.push('RRULE:FREQ=DAILY');
      icsContent.push('STATUS:CONFIRMED');
      icsContent.push('END:VEVENT');
    });

    // Optionally include meal reminders
    if (includeMealReminders && mealPlan) {
      const times = mealPlan.preferences?.meal_times || { breakfast: '08:00', lunch: '13:00', dinner: '20:00' };
      const slots = [
        { name: 'Breakfast', time: times.breakfast || '08:00' },
        { name: 'Lunch', time: times.lunch || '13:00' },
        { name: 'Dinner', time: times.dinner || '20:00' },
      ];

      slots.forEach((s) => {
        const [hh, mm] = s.time.split(':');
        const dtStart = `${now.getUTCFullYear()}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}T${hh || '08'}${mm || '00'}00Z`;
        icsContent.push('BEGIN:VEVENT');
        icsContent.push(`UID:meal-${s.name.toLowerCase()}@mednourish.local`);
        icsContent.push(`DTSTAMP:${timeStamp}`);
        icsContent.push(`DTSTART:${dtStart}`);
        icsContent.push(`SUMMARY:MedNourish Meal: ${s.name}`);
        icsContent.push(`DESCRIPTION:Daily meal reminder from your MedNourish meal planner.`);
        icsContent.push('RRULE:FREQ=DAILY');
        icsContent.push('STATUS:CONFIRMED');
        icsContent.push('END:VEVENT');
      });
    }

    icsContent.push('END:VCALENDAR');

    const blob = new Blob([icsContent.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mednourish_careplan_${now.toISOString().split('T')[0]}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const currentDay = mealPlan?.days?.[selectedDayIndex] || mealPlan?.days?.[0];

  const exerciseAndLifestyleTasks = tasks.filter((t) => t.is_auto);
  const manualTasks = tasks.filter((t) => !t.is_auto);

  return (
    <div className={styles.container}>
      {/* Top Header Bar */}
      <div className={styles.headerBar}>
        <div className={styles.titleArea}>
          <button type="button" onClick={onBackToDashboard} className={styles.backButton} aria-label="Back to Dashboard">
            <ArrowLeft size={16} /> Back
          </button>
          <CalendarCheck size={26} color="var(--color-primary)" />
          <h2 className={styles.title}>CarePlan Meal Planner & Wellness</h2>
        </div>

        <div className={styles.headerActions}>
          <p className={styles.generalFoodNote}>General food ideas, not a prescribed diet.</p>
        </div>
      </div>

      {/* Doctor Alert if applicable */}
      {mealPlan?.doctor_note && (
        <div className={styles.doctorAlertBox}>
          <AlertCircle size={18} />
          <span>{mealPlan.doctor_note}</span>
        </div>
      )}

      {/* Empty State when no assessments yet and no plan */}
      {!isLoading && (!mealPlan || mealPlan.days.length === 0) && (
        <div className={styles.emptyStateCard}>
          <Apple size={48} color="var(--color-primary)" />
          <h3 className={styles.emptyStateTitle}>Welcome to Your Personal Meal Planner</h3>
          <p className={styles.emptyStateDesc}>
            No screening report has been generated yet. Complete a guided symptom questionnaire or capture a photo to automatically tailor your 7-day meal plan to your specific nutritional signals.
          </p>
          <div className={styles.emptyActionsRow}>
            {onNavigateToView && (
              <>
                <button type="button" className={styles.navActionButton} onClick={() => onNavigateToView('medbot')}>
                  <Bot size={16} /> MedBot Assessment
                </button>
                <button type="button" className={styles.navActionButton} onClick={() => onNavigateToView('symptom-explorer')}>
                  <Search size={16} /> Symptom Explorer
                </button>
                <button type="button" className={styles.navActionButton} onClick={() => onNavigateToView('medscan-lite')}>
                  <Camera size={16} /> MedScan Image Check
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* 1) Day Tabs Strip & Preference Controls */}
      {mealPlan && mealPlan.days && mealPlan.days.length > 0 && (
        <>
          <div className={styles.dayTabsContainer} role="tablist" aria-label="Meal Plan Days">
            {mealPlan.days.map((day, idx) => {
              const isActive = idx === selectedDayIndex;
              const dateObj = new Date(day.date + 'T00:00:00');
              const formattedDate = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
              const labelName = idx === 0 ? 'Today' : idx === 1 ? 'Tomorrow' : day.day_name.slice(0, 3);

              return (
                <button
                  key={day.date}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`${styles.dayTab} ${isActive ? styles.dayTabActive : ''}`}
                  onClick={() => {
                    setSelectedDayIndex(idx);
                    fetchDayNutrients(day.date);
                  }}
                >
                  <span className={styles.dayTabName}>{labelName}</span>
                  <span className={styles.dayTabDate}>{formattedDate}</span>
                </button>
              );
            })}
          </div>

          <div className={styles.controlsBar}>
            <div className={styles.prefGroup}>
              <span className={styles.prefLabel}>Diet:</span>
              <select
                value={dietPref}
                onChange={(e) => handleUpdatePreferences(e.target.value, cuisinePref)}
                className={styles.selectInput}
                aria-label="Diet Preference"
              >
                <option value="veg">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="eggetarian">Eggetarian</option>
                <option value="nonveg">Non-Vegetarian</option>
              </select>

              <span className={styles.prefLabel} style={{ marginLeft: '0.75rem' }}>Cuisine:</span>
              <select
                value={cuisinePref}
                onChange={(e) => handleUpdatePreferences(dietPref, e.target.value)}
                className={styles.selectInput}
                aria-label="Cuisine Preference"
              >
                <option value="indian">Indian Everyday</option>
                <option value="global">Global Everyday</option>
                <option value="mixed">Mixed Variety</option>
              </select>
            </div>

            <button
              type="button"
              className={styles.regenButton}
              onClick={handleForceRegenerate}
              disabled={isRegenerating}
            >
              <RotateCw size={14} className={isRegenerating ? styles.spin : ''} />
              {isRegenerating ? 'Regenerating...' : 'Regenerate Plan'}
            </button>
          </div>

          {/* 2 & 3) Main Planner Grid (Left: Meals, Right: Nutrient Intake Today) */}
          {currentDay && (
            <div className={styles.plannerGrid}>
              {/* Left Column: Meal Cards */}
              <div className={styles.mealsColumn}>
                {(['breakfast', 'lunch', 'dinner'] as const).map((slot) => {
                  const slotData = currentDay.meals[slot];
                  if (!slotData) return null;
                  const key = `${currentDay.date}_${slot}`;
                  const chosenOptIndex = selectedOptions[key] ?? 0;
                  const isEaten = mealLogs[key] || false;
                  const slotTitle = slot.charAt(0).toUpperCase() + slot.slice(1);

                  return (
                    <div key={slot} className={styles.mealCard}>
                      <div className={styles.mealHeader}>
                        <div className={styles.mealTitleGroup}>
                          <Utensils size={18} color="var(--color-primary)" />
                          <h4 className={styles.mealTitle}>{slotTitle}</h4>
                        </div>
                        <span className={styles.mealBadge}>Choose 1 of 2</span>
                      </div>

                      {/* 2 Options */}
                      <div className={styles.optionsContainer}>
                        {slotData.options.map((opt) => {
                          const isSelected = chosenOptIndex === opt.option_index;
                          return (
                            <div
                              key={opt.food_id + opt.option_index}
                              className={`${styles.optionCard} ${isSelected ? styles.optionCardSelected : ''}`}
                              onClick={() => handleSelectOption(slot, opt.option_index)}
                              tabIndex={0}
                              role="radio"
                              aria-checked={isSelected}
                              onKeyDown={(e) => (e.key === ' ' || e.key === 'Enter') && handleSelectOption(slot, opt.option_index)}
                            >
                              <div className={styles.optionRadioRow}>
                                <input
                                  type="radio"
                                  name={`${currentDay.date}_${slot}_opt`}
                                  checked={isSelected}
                                  onChange={() => handleSelectOption(slot, opt.option_index)}
                                  aria-label={opt.name}
                                />
                                <p className={styles.optionName}>{opt.name}</p>
                              </div>
                              <p className={styles.optionNote}>{opt.prep_note}</p>

                              <div className={styles.coversRow}>
                                {opt.covers.map((c) => (
                                  <span key={c} className={styles.nutrientChipSmall}>
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Fruit on the Side */}
                      {slotData.fruit_side && slotData.fruit_side.length > 0 && (
                        <div className={styles.fruitSideRow}>
                          <Apple size={16} />
                          <span className={styles.fruitTag}>Fruit on the side:</span>
                          <span>
                            {slotData.fruit_side.map((f) => f.name).join(', ')}
                          </span>
                        </div>
                      )}

                      {/* Eaten Checkbox */}
                      <div className={styles.eatenRow}>
                        <label className={styles.eatenCheckboxLabel}>
                          <input
                            type="checkbox"
                            checked={isEaten}
                            onChange={() => handleToggleEaten(slot)}
                            className={styles.eatenCheckbox}
                          />
                          <span>Eaten today</span>
                        </label>
                        {isEaten && (
                          <span style={{ fontSize: '0.78rem', color: '#15803d', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <CheckCircle2 size={14} /> Completed
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Right Column: Nutrient Intake Today */}
              <div className={styles.intakePanel}>
                <h4 className={styles.intakeTitle}>Nutrient Intake Today</h4>

                <div className={styles.progressContainer}>
                  <div className={styles.progressBarOuter}>
                    <div
                      className={styles.progressBarInner}
                      style={{ width: `${Math.min(100, dayNutrients.progress_pct)}%` }}
                    />
                  </div>
                  <div className={styles.progressText}>
                    <span>{dayNutrients.covered.length} of {currentDay.nutrient_targets.length} targets</span>
                    <span>{Math.round(dayNutrients.progress_pct)}%</span>
                  </div>
                </div>

                <div className={styles.chipsSection}>
                  <p className={styles.chipsLabel}>Covered from Ticked Meals</p>
                  <div className={styles.chipsList}>
                    {dayNutrients.covered.length === 0 ? (
                      <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                        Tick meals eaten today to track coverage
                      </span>
                    ) : (
                      dayNutrients.covered.map((c) => (
                        <span key={c} className={styles.chipCovered}>
                          <Check size={12} /> {c}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                <div className={styles.chipsSection}>
                  <p className={styles.chipsLabel}>Pending Daily Targets</p>
                  <div className={styles.chipsList}>
                    {dayNutrients.pending.length === 0 ? (
                      <span style={{ fontSize: '0.8rem', color: '#15803d', fontWeight: 600 }}>
                        All daily targets covered!
                      </span>
                    ) : (
                      dayNutrients.pending.map((p) => (
                        <span key={p} className={styles.chipPending}>
                          {p}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* 4) Focus Nutrients Accordion */}
      {guidanceCards && guidanceCards.length > 0 && (
        <div className={styles.sectionCard}>
          <h3 className={styles.sectionTitle}>
            <Sparkles size={20} color="var(--color-primary)" />
            Focus Nutrients & Clinical Guidance
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {guidanceCards.map((card) => {
              const isExpanded = !!expandedAccordion[card.nutrient_id];
              return (
                <div key={card.nutrient_id} className={styles.accordionItem}>
                  <button
                    type="button"
                    className={styles.accordionHeader}
                    onClick={() => setExpandedAccordion((prev) => ({ ...prev, [card.nutrient_id]: !isExpanded }))}
                    aria-expanded={isExpanded}
                  >
                    <div className={styles.accordionTitleGroup}>
                      <span className={styles.accordionNutrientName}>{card.title}</span>
                      <span className={styles.accordionTriggerTag}>Identified in recent assessment</span>
                    </div>
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </button>

                  {isExpanded && (
                    <div className={styles.accordionBody}>
                      <div className={styles.guidanceBlock}>
                        <span className={styles.guidanceLabel}>Eat more:</span>
                        <p className={styles.guidanceText}>{card.eat_more}</p>
                      </div>

                      <div className={styles.guidanceBlock}>
                        <span className={styles.guidanceLabel}>Recommended fruits:</span>
                        <p className={styles.guidanceText}>{card.fruit_picks.join(', ')}</p>
                      </div>

                      <div className={styles.guidanceBlock}>
                        <span className={styles.guidanceLabel}>Habits to improve:</span>
                        <p className={styles.guidanceText}>{card.habits_to_improve}</p>
                      </div>

                      <div className={styles.guidanceBlock}>
                        <span className={styles.guidanceLabel}>Limit or avoid:</span>
                        <p className={styles.guidanceText}>{card.limit_or_avoid}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5) Exercise & Lifestyle Routines (Auto-Synced) */}
      {exerciseAndLifestyleTasks.length > 0 && (
        <div className={styles.sectionCard}>
          <h3 className={styles.sectionTitle}>
            <Activity size={20} color="var(--color-primary)" />
            Exercise & Lifestyle Habits
          </h3>
          <div className={styles.taskList}>
            {exerciseAndLifestyleTasks.map((t) => (
              <div key={t.id} className={styles.taskItem}>
                <div className={styles.taskLeft}>
                  <input
                    type="checkbox"
                    checked={t.is_completed}
                    onChange={() => handleToggleTaskComplete(t)}
                    className={styles.taskCheckbox}
                    aria-label={t.title}
                  />
                  <div>
                    <p className={`${styles.taskTitle} ${t.is_completed ? styles.taskCompleted : ''}`}>
                      {t.title}
                    </p>
                    <div className={styles.taskMeta}>
                      <span>Synced Habit</span>
                      <span>·</span>
                      <span>Daily</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5B) My Tasks (Manual CRUD) */}
      <div className={styles.sectionCard}>
        <h3 className={styles.sectionTitle}>
          <Plus size={20} color="var(--color-primary)" />
          My Wellness Tasks
        </h3>

        {taskErrorMessage && (
          <div style={{ color: '#b91c1c', background: '#fee2e2', padding: '0.6rem 0.85rem', borderRadius: '6px', fontSize: '0.85rem' }}>
            {taskErrorMessage}
          </div>
        )}

        <form onSubmit={handleCreateTask} className={styles.formRow}>
          <input
            type="text"
            placeholder="Add general wellness task (e.g., Drink 2L water, 30 min morning walk)..."
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className={styles.textInput}
            aria-label="New task title"
          />
          <select
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value as any)}
            className={styles.selectInput}
            aria-label="Task category"
          >
            <option value="water">Water</option>
            <option value="exercise">Exercise</option>
            <option value="sleep">Sleep</option>
            <option value="general">General</option>
          </select>
          <input
            type="time"
            value={newReminderTime}
            onChange={(e) => setNewReminderTime(e.target.value)}
            className={styles.selectInput}
            aria-label="Reminder time"
          />
          <button type="submit" disabled={isSubmittingTask} className={styles.primaryBtn}>
            <Plus size={16} /> Add Task
          </button>
        </form>

        <div className={styles.taskList} style={{ marginTop: '0.5rem' }}>
          {manualTasks.length === 0 ? (
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: '0.5rem 0' }}>
              No custom wellness tasks created yet.
            </p>
          ) : (
            manualTasks.map((t) => (
              <div key={t.id} className={styles.taskItem}>
                <div className={styles.taskLeft}>
                  <input
                    type="checkbox"
                    checked={t.is_completed}
                    onChange={() => handleToggleTaskComplete(t)}
                    className={styles.taskCheckbox}
                    aria-label={t.title}
                  />
                  <div>
                    <p className={`${styles.taskTitle} ${t.is_completed ? styles.taskCompleted : ''}`}>
                      {t.title}
                    </p>
                    <div className={styles.taskMeta}>
                      <span style={{ textTransform: 'capitalize' }}>{t.category}</span>
                      {t.reminder_time && (
                        <>
                          <span>·</span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                            <Clock size={12} /> {t.reminder_time}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleDeleteTask(t.id)}
                  style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: '0.3rem' }}
                  aria-label="Delete task"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 6) Calendar Export (.ics) */}
      <div className={styles.exportCard}>
        <div className={styles.exportOptions}>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={includeMealReminders}
              onChange={(e) => setIncludeMealReminders(e.target.checked)}
            />
            <span>Include meal reminders (Breakfast, Lunch, Dinner)</span>
          </label>
        </div>

        <button type="button" onClick={handleExportICS} className={styles.exportBtn}>
          <Download size={16} /> Export Schedule (.ics)
        </button>
      </div>
    </div>
  );
};
