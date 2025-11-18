# Writing RAG-Friendly Documentation

Best practices for creating documentation that works well with RAG systems.

---

## Core Principle

**Each section under a header should be understandable on its own, without requiring the reader to have read previous sections.**

RAG systems:
1. Break documents into chunks (500-1000 chars)
2. Retrieve chunks independently
3. May retrieve chunks out of order

---

## Key Guidelines

### 1. Self-Contained Sections

Each section should make sense independently.

**Bad:**
```markdown
## Step 2
Run the setup wizard and click Next three times.
```

**Good:**
```markdown
## Running the PostgreSQL Setup Wizard
Run the PostgreSQL setup wizard (postgresql-installer.exe):
1. Click Next on the welcome screen
2. Accept the default installation directory
3. Select components: Server, pgAdmin, CLI Tools
```

### 2. Include Topic in Headers

Mention the main subject in every H2/H3 header.

**Bad:**
```markdown
## Overview
## Installation
## Configuration
```

**Good:**
```markdown
## PostgreSQL Architecture Overview
## Installing PostgreSQL on Ubuntu
## PostgreSQL Connection Configuration
```

### 3. Adequate Section Length

**Target: 500-1500 characters per section**

- Too short (<200 chars): No context
- Too long (>2000 chars): Unfocused

### 4. Define Acronyms

Use "Full Term (Acronym)" pattern on first use.

**Bad:**
```markdown
Configure the WAL settings.
```

**Good:**
```markdown
Configure the WAL (Write-Ahead Logging) settings. PostgreSQL uses WAL to ensure data durability.
```

### 5. Avoid Pronouns

Use specific nouns instead of "it", "this", "that".

**Bad:**
```markdown
Download it from the website. Install it on your system.
```

**Good:**
```markdown
Download PostgreSQL from postgresql.org. Install PostgreSQL on your Ubuntu system.
```

### 6. Descriptive Cross-References

When linking, describe what's being referenced.

**Bad:**
```markdown
For more information, see the configuration section.
```

**Good:**
```markdown
For details on setting PostgreSQL authentication methods (md5, scram-sha-256), see the PostgreSQL Authentication Configuration section.
```

---

## Document Structure

### Optimal Document Size

**2,000 - 10,000 words per document**

- Too small (<500 words): Shallow chunks
- Too large (>20,000 words): Hard to maintain consistency

### Header Levels

**H1 (# Document Title)**
- 1 per document
- Contains main subject keywords

**H2 (## Major Sections)**
- 5-15 per document
- Full context (mention main subject)
- 300-800 words per section

**H3 (### Subsections)**
- As needed
- Specific topic + parent reference
- 150-400 words per section

**H4+ (#### Deep Nesting)**
- Use sparingly
- Deep nesting loses context

---

## Terminology Consistency

### Use Standard Terms

Pick one term for each concept and use it consistently.

**Bad:**
- Mix of "database", "DB", "data store"
- Mix of "configuration", "config", "settings"

**Good:**
- Always "database" (or always "DB")
- Always "configuration" (or always "config")

### Create a Glossary

```markdown
# Terminology Guide

**Authentication**: Use instead of "login verification"
**Configuration**: Use instead of "config" or "settings"
**Database**: Use instead of "DB" or "data store"
```

### Introduce Synonyms Once

When first using a term, mention common synonyms:

```markdown
PostgreSQL database configuration (also called Postgres config or DB settings) controls how your server operates.
```

---

## Anti-Patterns to Avoid

### Pronoun Overuse

```markdown
# Bad
Download it. Install it. Configure it.

# Good
Download PostgreSQL. Install PostgreSQL. Configure PostgreSQL.
```

### Implicit References

```markdown
# Bad
As mentioned above, edit the config file.

# Good
Edit the PostgreSQL configuration file (postgresql.conf) to modify connection settings.
```

### Single-Sentence Sections

```markdown
# Bad
## Backup
Regular backups are important.

# Good
## PostgreSQL Backup Strategy
Regular PostgreSQL backups are essential for data protection. Use pg_dump for logical backups or pg_basebackup for physical backups.

Example: `pg_dump mydatabase > backup.sql`
```

### Table-Only Content

```markdown
# Bad
## Configuration Options
| Option | Value |
|--------|-------|
| max_connections | 100 |

# Good
## PostgreSQL Memory Configuration
PostgreSQL memory settings control server performance. Key options:

| Option | Default | Description |
|--------|---------|-------------|
| max_connections | 100 | Maximum concurrent PostgreSQL connections |
| shared_buffers | 128MB | Memory buffer for caching data |

Increase shared_buffers for better query performance on systems with large RAM.
```

---

## Checklist

### Before Writing

- [ ] Define main topic
- [ ] List key search terms
- [ ] Check terminology standards
- [ ] Plan structure

### While Writing

- [ ] Include topic in headers
- [ ] Write complete sentences
- [ ] Define acronyms
- [ ] Aim for 500+ chars per section
- [ ] Repeat key terms
- [ ] Avoid pronouns
- [ ] Make cross-references descriptive

### After Writing

- [ ] Test each section independently
- [ ] Check term consistency
- [ ] Verify header descriptiveness
- [ ] Count section lengths
- [ ] Review acronym definitions

---

## Example: Before and After

### Before (RAG-Unfriendly)

```markdown
# Setup Guide

## Prerequisites
You need the latest version.

## Installation
1. Download it
2. Run the installer
3. Follow the steps

## Configuration
Edit the config file. Set the parameters mentioned earlier.
```

**Problems:**
- Generic headers
- No topic mentioned
- Vague pronouns
- Too short
- Implicit references

### After (RAG-Friendly)

```markdown
# PostgreSQL Database Setup Guide for Ubuntu

## Prerequisites for PostgreSQL Installation
Before installing PostgreSQL on Ubuntu, ensure:
- Ubuntu 20.04 or later
- At least 2GB RAM
- Sudo privileges
- Internet connection

Check version: `lsb_release -a`

## Installing PostgreSQL on Ubuntu
Install PostgreSQL using apt package manager:
1. Update packages: `sudo apt update`
2. Install: `sudo apt install postgresql postgresql-contrib`
3. Verify: `sudo systemctl status postgresql`

Service should show "active (running)".

## Configuring PostgreSQL Connection Settings
Configure connections in postgresql.conf at /etc/postgresql/14/main/:

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Key settings:
- **listen_addresses**: '0.0.0.0' for remote connections
- **port**: 5432 (default)
- **max_connections**: 100 (default)

Restart after changes: `sudo systemctl restart postgresql`
```

**Improvements:**
- Specific headers with "PostgreSQL" and "Ubuntu"
- 500-800 chars per section
- Acronyms defined
- No pronouns
- Self-contained sections

---

## Related Documentation

- **[RAG Guide](rag-guide.md)** - Complete RAG system guide
- **[Quality Evaluation](quality-evaluation.md)** - Measure documentation quality
