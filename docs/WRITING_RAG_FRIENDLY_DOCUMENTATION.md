# Writing RAG-Friendly Documentation

## A Complete Guide for Documentation Authors

This guide teaches you how to write documentation that works exceptionally well with RAG (Retrieval Augmented Generation) systems. Whether you're writing technical documentation, knowledge bases, or research notes, these principles will help your content be more discoverable and useful.

---

## Table of Contents

1. [Understanding RAG From a Writer's Perspective](#understanding-rag-from-a-writers-perspective)
2. [The Core Principle: Self-Contained Information Blocks](#the-core-principle-self-contained-information-blocks)
3. [Document Structure Best Practices](#document-structure-best-practices)
4. [How Much Information Per Header?](#how-much-information-per-header)
5. [Naming Conventions for RAG](#naming-conventions-for-rag)
6. [Linking and Cross-Referencing](#linking-and-cross-referencing)
7. [Handling Aliases and Synonyms](#handling-aliases-and-synonyms)
8. [Terminology Consistency](#terminology-consistency)
9. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
10. [RAG-Friendly Writing Checklist](#rag-friendly-writing-checklist)

---

## Understanding RAG From a Writer's Perspective

### How RAG Systems Read Your Documents

Unlike humans who read documents linearly from start to finish, RAG systems:

1. **Break your document into chunks** (typically 500-1000 characters)
2. **Convert each chunk to a semantic embedding** (a mathematical representation)
3. **Store chunks independently** in a vector database
4. **Retrieve relevant chunks** when answering questions
5. **May retrieve chunks out of order** or from different documents

**Key Insight:** Each chunk might be retrieved independently, without the surrounding context!

### Example: How a Human vs RAG Reads

**Your Document:**
```markdown
# Database Configuration

First, install PostgreSQL.

## Connection Settings

Set the host to localhost and port to 5432.
```

**Human reads:** "Oh, this is about PostgreSQL configuration"

**RAG retrieves:** Just the chunk "Set the host to localhost and port to 5432" without knowing it's about PostgreSQL!

**Better Version:**
```markdown
## PostgreSQL Connection Settings

Configure PostgreSQL database connection with these settings:
- Host: localhost
- Port: 5432
- Default database: postgres
```

Now the chunk is self-contained!

---

## The Core Principle: Self-Contained Information Blocks

### The Golden Rule

**Each section under a header should be understandable on its own, without requiring the reader to have read previous sections.**

### Example: Bad vs Good

❌ **Bad - Lacks Context:**
```markdown
# Installation

Download the installer.

## Step 2

Run the setup wizard and click Next three times.
```

The chunk "Run the setup wizard and click Next three times" doesn't mention what software this is for!

✅ **Good - Self-Contained:**
```markdown
# Installing PostgreSQL Database

Download the PostgreSQL installer from postgresql.org.

## Running the PostgreSQL Setup Wizard

Run the PostgreSQL setup wizard (postgresql-installer.exe):
1. Click Next on the welcome screen
2. Accept the default installation directory
3. Select components: PostgreSQL Server, pgAdmin, Command Line Tools
```

Each section mentions "PostgreSQL" so chunks remain identifiable.

---

## Document Structure Best Practices

### Optimal Document Size

**Target: 2,000 - 10,000 words per document**

- **Too small** (< 500 words): Creates shallow chunks with little information
- **Too large** (> 20,000 words): Makes it hard to maintain consistent topics
- **Just right**: Covers one major topic thoroughly

### Header Hierarchy Guidelines

#### Level 1 Headers (H1) - Document Title
```markdown
# PostgreSQL Database Administration Guide
```

- **Frequency:** 1 per document
- **Purpose:** Identifies the overall topic
- **Should contain:** The main subject matter keywords

#### Level 2 Headers (H2) - Major Sections
```markdown
## Installing PostgreSQL on Linux
## Configuring PostgreSQL Connection Settings
## PostgreSQL Backup and Recovery Procedures
```

- **Frequency:** 5-15 per document
- **Purpose:** Major subtopics
- **Should contain:** Full context (mention the main subject)
- **Ideal content size:** 300-800 words per section

#### Level 3 Headers (H3) - Subsections
```markdown
### Setting Up PostgreSQL Authentication with md5
### Creating PostgreSQL User Roles
```

- **Frequency:** As needed
- **Purpose:** Specific procedures or concepts
- **Should contain:** Specific topic + parent topic reference
- **Ideal content size:** 150-400 words per section

#### Level 4+ Headers - Use Sparingly

Deep nesting makes chunks too granular and lose context.

---

## How Much Information Per Header?

### The 500-Character Rule

**Each section should contain at least 500 characters** (roughly 100-150 words) of meaningful content.

### Optimal Section Length

**Target: 500-1500 characters per section (100-300 words)**

This creates chunks that:
- Contain complete thoughts
- Have enough context
- Aren't overwhelming

### Example Breakdown

✅ **Good Section Length:**
```markdown
## Configuring PostgreSQL Connection Pooling

PostgreSQL connection pooling manages database connections efficiently
by reusing existing connections instead of creating new ones. This
significantly improves application performance when handling many
concurrent database requests.

To configure connection pooling in PostgreSQL, use the PgBouncer tool:

1. Install PgBouncer: `sudo apt install pgbouncer`
2. Edit /etc/pgbouncer/pgbouncer.ini
3. Set pool_mode to 'transaction' for most applications
4. Configure max_client_conn based on your application's needs

For a typical web application, set max_client_conn to 100 and
default_pool_size to 20. This allows up to 100 client connections
sharing 20 actual PostgreSQL database connections.
```

**Length:** ~850 characters
**Why it works:** Complete explanation, actionable steps, specific examples

❌ **Too Short:**
```markdown
## Connection Pooling

Use PgBouncer. Set max_client_conn to 100.
```

**Length:** ~50 characters
**Problems:** No context, no explanation, unclear what PgBouncer is

---

## Naming Conventions for RAG

### Headers Should Be Descriptive and Specific

#### Bad Header Names
```markdown
## Overview
## Introduction
## Details
## Advanced Topics
## Troubleshooting
```

**Problem:** Generic names don't provide semantic value

#### Good Header Names
```markdown
## PostgreSQL Architecture Overview
## Introduction to PostgreSQL Replication
## PostgreSQL Performance Tuning Details
## Advanced PostgreSQL Query Optimization
## Troubleshooting PostgreSQL Connection Errors
```

**Why better:** Includes the main subject, making chunks discoverable

### File Naming

#### Bad File Names
```markdown
doc1.md
notes.md
guide.md
tutorial.md
```

#### Good File Names
```markdown
postgresql-installation-ubuntu.md
postgresql-backup-strategies.md
postgresql-performance-tuning.md
postgresql-replication-setup.md
```

**Pattern:** `[main-topic]-[specific-topic]-[context].md`

---

## Linking and Cross-Referencing

### Internal Links: Provide Context

When referencing other sections, **always provide a brief description** of what's being referenced.

❌ **Bad - Vague Reference:**
```markdown
For more information, see the configuration section.
```

✅ **Good - Descriptive Reference:**
```markdown
For more information on setting PostgreSQL authentication methods
(md5, scram-sha-256, trust), see the PostgreSQL Authentication
Configuration section.
```

**Why:** The chunk might be retrieved without the link, so the description provides value

### Cross-Document References

When referencing other documents, include key information inline.

❌ **Bad:**
```markdown
See postgresql-setup.md for installation instructions.
```

✅ **Good:**
```markdown
PostgreSQL installation requires downloading the installer from
postgresql.org and running the setup wizard. For detailed step-by-step
PostgreSQL installation instructions, see postgresql-setup.md.
```

### The "Echo Principle"

**Echo key information from linked documents so each chunk is self-sufficient.**

Example:
```markdown
## PostgreSQL Backup Strategies

PostgreSQL offers several backup strategies. The most common are:

### pg_dump - Logical Backups

pg_dump creates a logical backup by exporting database contents as
SQL statements. This is ideal for backing up individual PostgreSQL
databases.

Usage: `pg_dump dbname > backup.sql`

For physical backups using pg_basebackup, see the PostgreSQL Physical
Backup section in postgresql-backup-physical.md. Physical backups
copy the actual data files and are faster for large databases.
```

Notice how the cross-reference includes a brief explanation of what physical backups are.

---

## Handling Aliases and Synonyms

### The Alias Problem

Consider these terms that often mean the same thing:
- document / doc / file / resource
- database / DB / data store / repository
- configuration / config / settings / setup

**Problem for RAG:** A user searching for "database configuration" might miss chunks that only say "DB config"

### Solution 1: Establish Primary Terms

**Create a terminology document:**

```markdown
# Project Terminology Guide

## Standard Terms

Use these terms consistently:
- **Document**: Use instead of "doc", "file", "resource"
- **Database**: Use instead of "DB", "data store"
- **Configuration**: Use instead of "config", "settings"

## Acceptable Synonyms

These are acceptable for variety but use sparingly:
- "PostgreSQL database" and "Postgres database" (both okay)
- "Database server" and "DB server" (both okay)
```

### Solution 2: Introduce Synonyms in Context

When first introducing a term, mention its common synonyms:

```markdown
## PostgreSQL Database Configuration

PostgreSQL database configuration (also called Postgres config or
DB settings) controls how your PostgreSQL database server operates...
```

This helps RAG match queries using any of these terms.

### Solution 3: Use Full Terms, Parenthetical Acronyms

❌ **Bad - Acronym Without Definition:**
```markdown
Configure the WAL settings.
```

✅ **Good - Definition Included:**
```markdown
Configure the WAL (Write-Ahead Logging) settings. PostgreSQL uses
WAL to ensure data durability...
```

**Pattern:** `Full Term (Acronym)` on first use, then either works

### Solution 4: Keyword Frontloading

**Include common search terms in the first sentence:**

```markdown
## PostgreSQL Password Authentication

PostgreSQL password authentication methods (including md5, scram-sha-256,
and password auth) control how users prove their identity when connecting
to the PostgreSQL database server...
```

This sentence includes:
- "PostgreSQL password authentication"
- "md5, scram-sha-256, password auth" (specific methods)
- "PostgreSQL database server"

All likely search terms!

### Example: Document Management Terms

If your system uses "document", "doc", "file", and "resource" interchangeably:

**Option A - Pick One Term:**
```markdown
# Document Management System

This document management system stores documents in PostgreSQL.
Each document has metadata...

[Use "document" consistently throughout]
```

**Option B - Acknowledge Aliases:**
```markdown
# Document Management System

This document management system (sometimes called doc manager,
file repository, or resource store) helps you organize documents.

Each document (file/resource) in the system has metadata...
```

**Option A is better** for RAG because consistency improves matching.

---

## Terminology Consistency

### The Consistency Principle

**Use the same term for the same concept throughout your documentation.**

### Creating a Glossary

Maintain a glossary document:

```markdown
# Documentation Glossary

## A

**Authentication**: The process of verifying user identity in PostgreSQL.
Use this term instead of "login verification" or "identity check".

**Authorization**: The process of determining user permissions in PostgreSQL.
Use this term instead of "access control" or "permission checking".

## C

**Configuration**: PostgreSQL server settings. Use this term instead of
"config" or "setup" except in filenames like postgresql.conf.

**Connection**: A link between a client and PostgreSQL server. Use this
term instead of "session" (session has a different meaning in PostgreSQL).
```

### Consistent Term Patterns

#### Example: User Management

Pick one pattern and stick to it:

**Pattern A:**
- Create user
- Delete user
- Modify user
- List users

**Pattern B:**
- Add user
- Remove user
- Edit user
- Show users

**Don't mix:** "Create user", "Remove user", "Edit user" (inconsistent verbs)

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Pronoun Overuse

**Bad:**
```markdown
## Installation

Download it from the website. Install it on your system. Then configure it.
```

**Good:**
```markdown
## PostgreSQL Installation

Download PostgreSQL from postgresql.org. Install PostgreSQL on your
Ubuntu system using apt. Then configure PostgreSQL connection settings.
```

### ❌ Anti-Pattern 2: Implicit References

**Bad:**
```markdown
## Step 2

As mentioned above, the configuration file needs to be edited.
```

**Good:**
```markdown
## Step 2: Edit PostgreSQL Configuration

Edit the PostgreSQL configuration file (postgresql.conf) to modify
connection settings as described in Step 1.
```

### ❌ Anti-Pattern 3: Single-Sentence Sections

**Bad:**
```markdown
## Backup

Regular backups are important.

## Restore

Use restore to recover data.
```

**Good:**
```markdown
## PostgreSQL Backup Strategy

Regular PostgreSQL backups are essential for data protection. Use
pg_dump for logical backups of individual databases, or pg_basebackup
for physical backups of the entire PostgreSQL cluster.

Example: `pg_dump mydatabase > backup.sql`

## PostgreSQL Database Restore

To restore a PostgreSQL database from a pg_dump backup, use the psql
command with input redirection: `psql mydatabase < backup.sql`

This restores all tables, data, and schema from the backup file to the
specified PostgreSQL database.
```

### ❌ Anti-Pattern 4: Table-Only Content

**Bad:**
```markdown
## Configuration Options

| Option | Value |
|--------|-------|
| max_connections | 100 |
| shared_buffers | 128MB |
```

**Good:**
```markdown
## PostgreSQL Memory Configuration Options

PostgreSQL memory settings control database server performance. Key
configuration options in postgresql.conf:

| Option | Default | Description |
|--------|---------|-------------|
| max_connections | 100 | Maximum number of concurrent PostgreSQL client connections |
| shared_buffers | 128MB | PostgreSQL shared memory buffer size for caching data |

Increase shared_buffers for better PostgreSQL query performance on
systems with large amounts of RAM.
```

### ❌ Anti-Pattern 5: Context in Separate File

**Bad Structure:**
```
prerequisites.md  <- Contains "You need PostgreSQL 12+"
tutorial.md       <- Contains steps but no version info
```

**Good Structure:**
```
postgresql-tutorial.md  <- Contains prerequisites AND steps
```

Or:

```
postgresql-tutorial.md:
## Prerequisites for PostgreSQL Tutorial
This tutorial requires PostgreSQL 12 or higher...

## Step 1: Configure PostgreSQL
First, configure PostgreSQL connection settings...
```

---

## RAG-Friendly Writing Checklist

### Before Writing

- [ ] **Define main topic** - What is this document about?
- [ ] **List key terms** - What terms will users search for?
- [ ] **Check glossary** - What are the standard terms to use?
- [ ] **Plan structure** - How will you organize information?

### While Writing

- [ ] **Include topic in headers** - Every H2/H3 mentions the main subject
- [ ] **Write complete sentences** - Avoid fragments and abbreviations
- [ ] **Define acronyms** - Use "Full Term (Acronym)" pattern
- [ ] **Aim for 500+ chars per section** - Enough content for meaningful chunks
- [ ] **Repeat key terms** - Use main topic terms multiple times per section
- [ ] **Front-load keywords** - Put important terms in first sentences
- [ ] **Avoid pronouns** - Use specific nouns instead of "it", "this", "that"
- [ ] **Make cross-references descriptive** - Explain what's being linked

### After Writing

- [ ] **Test each section independently** - Can it stand alone?
- [ ] **Check term consistency** - Same terms for same concepts?
- [ ] **Verify header descriptiveness** - Are headers specific and searchable?
- [ ] **Count section lengths** - Are sections 500-1500 characters?
- [ ] **Review acronym definitions** - All acronyms defined on first use?
- [ ] **Check for implicit references** - Any unclear "as mentioned above"?

---

## Practical Example: Before and After

### Before: RAG-Unfriendly Version

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

## Usage

Now you can use it. See the examples.
```

**Problems:**
- Generic headers ("Setup Guide", "Prerequisites")
- No topic mentioned (what software?)
- Vague pronouns ("it", "the steps")
- Too short (sections are 10-50 chars)
- Implicit references ("mentioned earlier", "the examples")

---

### After: RAG-Friendly Version

```markdown
# PostgreSQL Database Setup Guide for Ubuntu Linux

This guide walks through installing and configuring PostgreSQL database
server on Ubuntu Linux systems.

## Prerequisites for PostgreSQL Installation

Before installing PostgreSQL on Ubuntu Linux, ensure your system meets
these requirements:

- Ubuntu 20.04 or later
- At least 2GB RAM for PostgreSQL server
- Sudo privileges for installing PostgreSQL packages
- Internet connection to download PostgreSQL from apt repositories

Check your Ubuntu version: `lsb_release -a`

## Installing PostgreSQL Database Server on Ubuntu

Follow these steps to install PostgreSQL database server on Ubuntu Linux
using the apt package manager:

1. Update Ubuntu package lists: `sudo apt update`
2. Install PostgreSQL: `sudo apt install postgresql postgresql-contrib`
3. Verify PostgreSQL installation: `sudo systemctl status postgresql`

PostgreSQL service should show as "active (running)" after installation.
The default PostgreSQL installation creates a 'postgres' user and a
'postgres' database.

## Configuring PostgreSQL Connection Settings

After installing PostgreSQL, configure connection settings in the
postgresql.conf file located at /etc/postgresql/14/main/postgresql.conf:

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Key PostgreSQL connection settings to configure:

- **listen_addresses**: Set to '0.0.0.0' to allow remote PostgreSQL connections
- **port**: Default PostgreSQL port is 5432
- **max_connections**: Maximum concurrent PostgreSQL connections (default: 100)

Restart PostgreSQL after changing configuration: `sudo systemctl restart postgresql`

## Using PostgreSQL After Installation

Once PostgreSQL is installed and configured, you can connect to the
PostgreSQL database using the psql command-line tool:

```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# Create a new PostgreSQL database
CREATE DATABASE myapp;

# Create a new PostgreSQL user
CREATE USER myuser WITH PASSWORD 'mypassword';

# Grant PostgreSQL privileges
GRANT ALL PRIVILEGES ON DATABASE myapp TO myuser;
```

For detailed PostgreSQL SQL command examples, see the PostgreSQL Query
Tutorial document (postgresql-queries.md).
```

**Improvements:**
- Specific title: "PostgreSQL Database Setup Guide for Ubuntu Linux"
- Every header mentions "PostgreSQL" and/or "Ubuntu"
- Sections are 500-800 characters each
- Acronyms defined: RAM, SQL
- No pronouns - "PostgreSQL" used throughout
- Complete, self-contained sections
- Cross-reference includes description of linked content
- Technical terms consistent: "PostgreSQL" not "Postgres" or "PG"

---

## Measuring RAG-Friendliness

See the companion document `DOCUMENT_DESIGN_EVALUATION.md` for reproducible
metrics to evaluate your documentation design.

### Quick Self-Assessment

For each section, ask:

1. **Can I understand this section without reading anything else?**
2. **Does this section mention the main topic at least once?**
3. **Is this section at least 500 characters?**
4. **Have I avoided pronouns like "it", "this", "that"?**
5. **Are my terms consistent with the glossary?**

If you answer "no" to any question, revise that section.

---

## Summary: The Core Principles

1. **Self-Contained Sections**: Each section should make sense independently
2. **Explicit Topics**: Mention the main topic in every header
3. **Adequate Length**: 500-1500 characters per section
4. **Term Consistency**: Use the same words for the same concepts
5. **Keyword Frontloading**: Put important terms early in sections
6. **Synonym Introduction**: Define aliases when first mentioned
7. **Descriptive Links**: Explain what you're linking to
8. **Avoid Pronouns**: Use specific nouns instead of "it"
9. **Define Acronyms**: "Full Term (Acronym)" on first use
10. **Descriptive Headers**: Make headers specific and searchable

---

## Further Reading

- `RAG_DATA_PREPARATION_GUIDE.md` - Understanding the RAG pipeline
- `DOCUMENT_DESIGN_EVALUATION.md` - Metrics for evaluating your docs
- `PREPROCESSOR_QUICKSTART.md` - Testing your documents with the preprocessor

---

**Remember:** You're not just writing for humans who read linearly - you're
writing for a RAG system that will chunk, embed, and retrieve your content
in unpredictable ways. Make each chunk valuable on its own!
