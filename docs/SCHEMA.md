# clibo schema

Auto-generated reference for every SQLite table clibo writes to. Regenerate with `python scripts/dump_schema.py`.

_86 tables in total._

## Contents

- [Core](#core)
- [Health & Wellness](#health--wellness)
- [Money & Finance](#money--finance)
- [Productivity & Work](#productivity--work)
- [CRM & Relationships](#crm--relationships)
- [Home & Life](#home--life)
- [Hobbies & Culture](#hobbies--culture)

## Core

### `clibo_setting`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `scope` | `VARCHAR` | NOT NULL, indexed |
| `key` | `VARCHAR` | NOT NULL, indexed |
| `value` | `VARCHAR` | NOT NULL |

### `document_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, default |
| `expires` | `DATE` | NOT NULL, indexed |
| `issued` | `DATE` | — |
| `number` | `VARCHAR` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `donation_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `recipient` | `VARCHAR` | NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `tax_deductible` | `BOOLEAN` | NOT NULL, default |
| `receipt` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `fast_session`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `start_time` | `DATETIME` | NOT NULL, indexed |
| `end_time` | `DATETIME` | — |
| `target_hours` | `FLOAT` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `package_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `sender` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `tracking_number` | `VARCHAR` | — |
| `carrier` | `VARCHAR` | — |
| `ordered_date` | `DATE` | NOT NULL, default |
| `expected_date` | `DATE` | — |
| `received_date` | `DATE` | — |
| `status` | `VARCHAR` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `step_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `count` | `INTEGER` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `source` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `stretch_session`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `area` | `VARCHAR` | NOT NULL, default |
| `duration_min` | `INTEGER` | NOT NULL, default |
| `poses` | `VARCHAR` | — |
| `difficulty` | `INTEGER` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

## Health & Wellness

### `caffeine_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `drink` | `VARCHAR` | NOT NULL |
| `mg` | `INTEGER` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `consumed_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `calorie_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `food` | `VARCHAR` | NOT NULL |
| `kcal` | `INTEGER` | NOT NULL |
| `protein` | `FLOAT` | NOT NULL, default |
| `carbs` | `FLOAT` | NOT NULL, default |
| `fat` | `FLOAT` | NOT NULL, default |
| `meal` | `VARCHAR` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `meditate_session`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `minutes` | `INTEGER` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `meds_dose`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `med_id` | `INTEGER` | NOT NULL, indexed |
| `taken_at` | `DATETIME` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `note` | `VARCHAR` | — |

### `meds_medication`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `dosage` | `VARCHAR` | — |
| `times_per_day` | `INTEGER` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `active` | `BOOLEAN` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `mood_log`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `score` | `INTEGER` | NOT NULL |
| `emotion` | `VARCHAR` | — |
| `note` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `period_log`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `start_date` | `DATE` | NOT NULL, indexed |
| `end_date` | `DATE` | — |
| `flow` | `VARCHAR` | — |
| `symptoms` | `VARCHAR` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `sleep_log`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `hours` | `FLOAT` | NOT NULL |
| `quality` | `INTEGER` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `bedtime` | `VARCHAR` | — |
| `wake_time` | `VARCHAR` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `vitals_reading`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, indexed |
| `value` | `FLOAT` | NOT NULL |
| `value2` | `FLOAT` | — |
| `unit` | `VARCHAR` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `water_log`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `amount_ml` | `INTEGER` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `weight_log`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `weight_kg` | `FLOAT` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `workout_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `exercise` | `VARCHAR` | NOT NULL |
| `sets` | `INTEGER` | NOT NULL, default |
| `reps` | `INTEGER` | NOT NULL, default |
| `weight_kg` | `FLOAT` | NOT NULL, default |
| `duration_min` | `INTEGER` | NOT NULL, default |
| `kcal_burned` | `INTEGER` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

## Money & Finance

### `bills_bill`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `amount` | `FLOAT` | NOT NULL, default |
| `due_date` | `DATE` | NOT NULL, indexed |
| `category` | `VARCHAR` | NOT NULL, default |
| `paid` | `BOOLEAN` | NOT NULL, default |
| `paid_date` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `budget_limit`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `category` | `VARCHAR` | NOT NULL, indexed |
| `monthly_limit` | `FLOAT` | NOT NULL |
| `created_at` | `DATETIME` | NOT NULL, default |

### `debt_debt`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `principal` | `FLOAT` | NOT NULL |
| `creditor` | `VARCHAR` | — |
| `apr` | `FLOAT` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `debt_payment`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `debt_id` | `INTEGER` | NOT NULL, indexed |
| `amount` | `FLOAT` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `expense_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `description` | `VARCHAR` | NOT NULL |
| `category` | `VARCHAR` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `income_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `source` | `VARCHAR` | NOT NULL |
| `category` | `VARCHAR` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `invest_latest_price`

| Column | Type | Notes |
|---|---|---|
| `ticker` | `VARCHAR` | PK, NOT NULL |
| `price` | `FLOAT` | NOT NULL |
| `updated_at` | `DATETIME` | NOT NULL, default |

### `invest_transaction`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `ticker` | `VARCHAR` | NOT NULL, indexed |
| `kind` | `VARCHAR` | NOT NULL, default |
| `action` | `VARCHAR` | NOT NULL, default |
| `shares` | `FLOAT` | NOT NULL |
| `price_per_share` | `FLOAT` | NOT NULL |
| `txn_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `invoice_invoice`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `number` | `VARCHAR` | NOT NULL |
| `client` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `amount` | `FLOAT` | NOT NULL |
| `tax_pct` | `FLOAT` | NOT NULL, default |
| `issued` | `DATE` | NOT NULL, default |
| `due` | `DATE` | — |
| `status` | `VARCHAR` | NOT NULL, default |
| `paid_date` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `networth_item`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `category` | `VARCHAR` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `updated_at` | `DATETIME` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `networth_snapshot`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `total_assets` | `FLOAT` | NOT NULL |
| `total_liabilities` | `FLOAT` | NOT NULL |
| `net_worth` | `FLOAT` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `savings_deposit`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `goal_id` | `INTEGER` | NOT NULL, indexed |
| `amount` | `FLOAT` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `savings_goal`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `target` | `FLOAT` | NOT NULL |
| `deadline` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `split_expense`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `description` | `VARCHAR` | NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `paid_by` | `VARCHAR` | NOT NULL |
| `participants` | `VARCHAR` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `split_settlement`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `from_person` | `VARCHAR` | NOT NULL |
| `to_person` | `VARCHAR` | NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `subs_subscription`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `amount` | `FLOAT` | NOT NULL |
| `cycle` | `VARCHAR` | NOT NULL, default |
| `category` | `VARCHAR` | NOT NULL, default |
| `next_billing` | `DATE` | — |
| `active` | `BOOLEAN` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `tip_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `bill_amount` | `FLOAT` | NOT NULL |
| `tip_amount` | `FLOAT` | NOT NULL |
| `tip_percent` | `FLOAT` | NOT NULL |
| `venue` | `VARCHAR` | — |
| `service_rating` | `INTEGER` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `wishlist_item`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `price` | `FLOAT` | NOT NULL, default |
| `priority` | `INTEGER` | NOT NULL, default |
| `url` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `purchased` | `BOOLEAN` | NOT NULL, default |
| `purchased_date` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

## Productivity & Work

### `bookmark_bookmark`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `url` | `VARCHAR` | NOT NULL |
| `title` | `VARCHAR` | — |
| `tags` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `favorite` | `BOOLEAN` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `challenge_checkin`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `challenge_id` | `INTEGER` | NOT NULL, indexed |
| `check_date` | `DATE` | NOT NULL, indexed |
| `success` | `BOOLEAN` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `challenge_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `start_date` | `DATE` | NOT NULL |
| `target_days` | `INTEGER` | NOT NULL |
| `miss_budget` | `INTEGER` | NOT NULL, default |
| `status` | `VARCHAR` | NOT NULL, default |
| `finished_at` | `DATE` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `events_event`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `event_date` | `DATE` | NOT NULL, indexed |
| `event_time` | `VARCHAR` | — |
| `location` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `focus_session`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `task` | `VARCHAR` | — |
| `minutes` | `INTEGER` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `goals_goal`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `deadline` | `DATE` | — |
| `done` | `BOOLEAN` | NOT NULL, default |
| `done_at` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `goals_milestone`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `goal_id` | `INTEGER` | NOT NULL, indexed |
| `name` | `VARCHAR` | NOT NULL |
| `done` | `BOOLEAN` | NOT NULL, default |
| `done_at` | `DATE` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `habit_check`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `habit_id` | `INTEGER` | NOT NULL, indexed |
| `check_date` | `DATE` | NOT NULL, indexed, default |

### `habit_habit`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `target_per_week` | `INTEGER` | NOT NULL, default |
| `active` | `BOOLEAN` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `ideas_idea`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `status` | `VARCHAR` | NOT NULL, default |
| `tags` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |
| `updated_at` | `DATETIME` | NOT NULL, default |

### `journal_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `body` | `VARCHAR` | NOT NULL |
| `mood` | `INTEGER` | — |
| `tags` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |
| `updated_at` | `DATETIME` | NOT NULL, default |

### `notes_note`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `body` | `VARCHAR` | NOT NULL, default |
| `tags` | `VARCHAR` | — |
| `pinned` | `BOOLEAN` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `updated_at` | `DATETIME` | NOT NULL, default |

### `time_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `project` | `VARCHAR` | NOT NULL |
| `task` | `VARCHAR` | — |
| `minutes` | `INTEGER` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `time_timer`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `project` | `VARCHAR` | NOT NULL |
| `task` | `VARCHAR` | — |
| `started_at` | `DATETIME` | NOT NULL, default |

### `todo_task`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `priority` | `VARCHAR` | NOT NULL, default |
| `due` | `DATE` | — |
| `done` | `BOOLEAN` | NOT NULL, default |
| `done_at` | `DATE` | — |
| `project` | `VARCHAR` | — |
| `tags` | `VARCHAR` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `worklog_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `summary` | `VARCHAR` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, default |
| `project` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

## CRM & Relationships

### `birthdays_occasion`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `person` | `VARCHAR` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, default |
| `month` | `INTEGER` | NOT NULL |
| `day` | `INTEGER` | NOT NULL |
| `year` | `INTEGER` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `brag_achievement`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `impact` | `VARCHAR` | — |
| `tags` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `clients_client`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `company` | `VARCHAR` | — |
| `email` | `VARCHAR` | — |
| `hourly_rate` | `FLOAT` | NOT NULL, default |
| `status` | `VARCHAR` | NOT NULL, default |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `clients_hours`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `client_id` | `INTEGER` | NOT NULL, indexed |
| `hours` | `FLOAT` | NOT NULL |
| `description` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `crm_contact`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `company` | `VARCHAR` | — |
| `email` | `VARCHAR` | — |
| `phone` | `VARCHAR` | — |
| `tags` | `VARCHAR` | — |
| `status` | `VARCHAR` | NOT NULL, default |
| `notes` | `VARCHAR` | — |
| `last_contact` | `DATE` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `cv_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `org` | `VARCHAR` | — |
| `kind` | `VARCHAR` | NOT NULL, default |
| `start_date` | `DATE` | — |
| `end_date` | `DATE` | — |
| `location` | `VARCHAR` | — |
| `description` | `VARCHAR` | — |
| `achievements` | `VARCHAR` | — |
| `tags` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `followup_followup`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `person` | `VARCHAR` | NOT NULL |
| `reason` | `VARCHAR` | — |
| `due_date` | `DATE` | NOT NULL, indexed |
| `done` | `BOOLEAN` | NOT NULL, default |
| `done_at` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `gifts_gift`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `recipient` | `VARCHAR` | NOT NULL |
| `idea` | `VARCHAR` | NOT NULL |
| `occasion` | `VARCHAR` | — |
| `price` | `FLOAT` | NOT NULL, default |
| `status` | `VARCHAR` | NOT NULL, default |
| `url` | `VARCHAR` | — |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `jobs_application`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `company` | `VARCHAR` | NOT NULL |
| `role` | `VARCHAR` | NOT NULL |
| `status` | `VARCHAR` | NOT NULL, default |
| `applied_date` | `DATE` | NOT NULL, default |
| `salary` | `VARCHAR` | — |
| `location` | `VARCHAR` | — |
| `url` | `VARCHAR` | — |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `leads_lead`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `contact` | `VARCHAR` | — |
| `value` | `FLOAT` | NOT NULL, default |
| `stage` | `VARCHAR` | NOT NULL, default |
| `expected_close` | `DATE` | — |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `meetings_action`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `meeting_id` | `INTEGER` | NOT NULL, indexed |
| `summary` | `VARCHAR` | NOT NULL |
| `owner` | `VARCHAR` | — |
| `done` | `BOOLEAN` | NOT NULL, default |
| `done_at` | `DATE` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `meetings_meeting`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `meeting_date` | `DATE` | NOT NULL, indexed, default |
| `attendees` | `VARCHAR` | — |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `network_connection`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `company` | `VARCHAR` | — |
| `met_where` | `VARCHAR` | — |
| `context` | `VARCHAR` | — |
| `met_date` | `DATE` | NOT NULL, indexed, default |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

## Home & Life

### `car_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `kind` | `VARCHAR` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `odometer` | `INTEGER` | — |
| `volume` | `FLOAT` | — |
| `cost` | `FLOAT` | NOT NULL, default |
| `service` | `VARCHAR` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `chores_chore`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `frequency_days` | `INTEGER` | NOT NULL, default |
| `assignee` | `VARCHAR` | — |
| `last_done` | `DATE` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `groceries_item`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `quantity` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `bought` | `BOOLEAN` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `home_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, default |
| `cost` | `FLOAT` | NOT NULL, default |
| `location` | `VARCHAR` | — |
| `contractor` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `meals_plan`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `plan_date` | `DATE` | NOT NULL, indexed |
| `meal_type` | `VARCHAR` | NOT NULL |
| `dish` | `VARCHAR` | NOT NULL |
| `created_at` | `DATETIME` | NOT NULL, default |

### `pantry_item`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `quantity` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `location` | `VARCHAR` | NOT NULL, default |
| `expiry` | `DATE` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `pets_event`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `pet_id` | `INTEGER` | NOT NULL, indexed |
| `kind` | `VARCHAR` | NOT NULL |
| `summary` | `VARCHAR` | NOT NULL |
| `cost` | `FLOAT` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `pets_pet`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `species` | `VARCHAR` | — |
| `breed` | `VARCHAR` | — |
| `birth` | `DATE` | — |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `plants_plant`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `species` | `VARCHAR` | — |
| `water_every_days` | `INTEGER` | NOT NULL, default |
| `last_watered` | `DATE` | — |
| `location` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `recipes_recipe`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `ingredients` | `VARCHAR` | — |
| `instructions` | `VARCHAR` | — |
| `servings` | `INTEGER` | — |
| `prep_minutes` | `INTEGER` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `tags` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `travel_event`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `trip_id` | `INTEGER` | NOT NULL, indexed |
| `event_date` | `DATE` | NOT NULL |
| `event_time` | `VARCHAR` | — |
| `title` | `VARCHAR` | NOT NULL |
| `location` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `cost` | `FLOAT` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `travel_trip`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `name` | `VARCHAR` | NOT NULL |
| `destination` | `VARCHAR` | — |
| `start_date` | `DATE` | — |
| `end_date` | `DATE` | — |
| `budget` | `FLOAT` | NOT NULL, default |
| `notes` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

## Hobbies & Culture

### `books_book`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `author` | `VARCHAR` | — |
| `status` | `VARCHAR` | NOT NULL, default |
| `pages` | `INTEGER` | NOT NULL, default |
| `pages_read` | `INTEGER` | NOT NULL, default |
| `rating` | `INTEGER` | — |
| `started` | `DATE` | — |
| `finished` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `dreams_dream`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `summary` | `VARCHAR` | NOT NULL |
| `description` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `vividness` | `INTEGER` | NOT NULL, default |
| `lucid` | `BOOLEAN` | NOT NULL, default |
| `symbols` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `films_film`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `title` | `VARCHAR` | NOT NULL |
| `kind` | `VARCHAR` | NOT NULL, default |
| `year` | `INTEGER` | — |
| `status` | `VARCHAR` | NOT NULL, default |
| `rating` | `INTEGER` | — |
| `watched_on` | `DATE` | — |
| `note` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |

### `flashcards_card`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `front` | `VARCHAR` | NOT NULL |
| `back` | `VARCHAR` | NOT NULL |
| `deck` | `VARCHAR` | NOT NULL, default |
| `box` | `INTEGER` | NOT NULL, default |
| `next_review` | `DATE` | NOT NULL, indexed, default |
| `reviews` | `INTEGER` | NOT NULL, default |
| `correct` | `INTEGER` | NOT NULL, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `gratitude_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `text` | `VARCHAR` | NOT NULL |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `lessons_lesson`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `takeaway` | `VARCHAR` | NOT NULL |
| `context` | `VARCHAR` | — |
| `category` | `VARCHAR` | NOT NULL, default |
| `tags` | `VARCHAR` | — |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |

### `mileage_entry`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `activity` | `VARCHAR` | NOT NULL, default |
| `distance_km` | `FLOAT` | NOT NULL |
| `duration_min` | `INTEGER` | NOT NULL, default |
| `entry_date` | `DATE` | NOT NULL, indexed, default |
| `created_at` | `DATETIME` | NOT NULL, default |
| `note` | `VARCHAR` | — |

### `quotes_quote`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | PK, NOT NULL |
| `text` | `VARCHAR` | NOT NULL |
| `author` | `VARCHAR` | — |
| `source` | `VARCHAR` | — |
| `tags` | `VARCHAR` | — |
| `created_at` | `DATETIME` | NOT NULL, default |
