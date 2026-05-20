# Telegram Coaching Bot

A private Telegram coaching platform where coaches manage athletes and assign workouts.

## Architecture

```
coachbot/
├── bot.py              # Application entry point
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── handlers/           # Message and callback routers
│   ├── __init__.py
│   ├── message_handlers.py    # /start, /help, etc.
│   └── callback_handlers.py   # Button interactions
├── services/           # Business logic layer
│   ├── __init__.py
│   └── business_services.py   # Coach, Workout, Exercise services
├── storage/            # Data persistence layer
│   ├── __init__.py
│   └── in_memory.py           # In-memory storage (dev only)
├── keyboards/          # UI keyboard builders
│   ├── __init__.py
│   └── inline_keyboards.py    # Inline keyboard constructors
├── models/             # Domain entities
│   ├── __init__.py
│   └── entities.py            # Coach, Athlete, Workout, etc.
├── docs/               # Documentation
└── media/              # Static media files
```

## Module Responsibilities

### `config.py`
- Environment variable loading
- Application settings (bot token, log level)
- Singleton configuration access

### `handlers/`
- **message_handlers.py**: Routes incoming text messages and commands
- **callback_handlers.py**: Handles inline button callbacks
- Clean separation: handlers only parse input and call services

### `services/`
- **business_services.py**: Core business logic
  - `CoachService`: Coach registration, athlete management
  - `WorkoutService`: Workout creation and management
  - `ExerciseService`: Exercise session tracking
- Services coordinate between handlers and storage

### `storage/`
- **in_memory.py**: Dictionary-based data store for development
- Provides CRUD operations for all entities
- Will be replaced with database backend in production

### `keyboards/`
- **inline_keyboards.py**: Reusable keyboard builders
- Consistent UI patterns across the bot
- No business logic, only UI construction

### `models/`
- **entities.py**: Pure data classes (no DB ties)
- Domain entities: Coach, Athlete, Workout, Block, Exercise, ExerciseSession
- Type-safe data structures

## Running the Bot

1. Set environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python bot.py
   ```

## Next Steps (Not Implemented Yet)

- [ ] Database integration (SQLite/PostgreSQL)
- [ ] Stateful conversations (FSM)
- [ ] Video upload handling
- [ ] Coach notifications for help requests
- [ ] Workout builder interface
- [ ] Role-based access (coach vs athlete)
- [ ] Error handling and retry logic
- [ ] Unit tests

## Design Principles

1. **Separation of Concerns**: Handlers → Services → Storage
2. **Modular**: Each module has a single responsibility
3. **Testable**: Services can be tested without Telegram
4. **Extensible**: Easy to add new features without breaking existing code
5. **Production-Ready Structure**: Ready for database, logging, monitoring
