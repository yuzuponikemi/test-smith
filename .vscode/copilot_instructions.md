# **Standing Instructions: Modern Python Project Management with uv**

This document outlines the strict, mandatory guidelines for managing Python projects. The **sole and exclusive tool** for all virtual environment and package management tasks is **uv**.

The primary workflow is based on defining direct dependencies in a requirements.in file and generating a locked requirements.txt file for reproducible installs.

### **Golden Rule: uv is the Only Tool**

For any task involving Python virtual environments or packages, you **MUST** use the uv command-line tool. You **MUST NOT** use python \-m venv, pip, or any other package manager unless explicitly instructed for a specific, exceptional reason.

## **The Core Workflow: Intent \-\> Lock \-\> Sync**

This three-step process is the standard for all projects.

### **Step 1: Define Direct Dependencies in requirements.in**

The project's direct, top-level dependencies **MUST** be declared in a file named requirements.in. This file is for human authors to declare the project's *intent*. Version specifiers can be flexible.

**✅ Example requirements.in:**

\# This file lists the packages my project \*directly\* depends on.  
pandas  
fastapi\>=0.100  
httpx\[http2\]

### **Step 2: Generate a Lockfile with uv pip compile**

After modifying requirements.in, you **MUST** generate a complete and pinned lockfile named requirements.txt. This file is machine-generated and ensures deterministic, reproducible builds.

**✅ DO THIS:**

uv pip compile requirements.in \-o requirements.txt

The resulting requirements.txt will contain every direct and transitive dependency with a pinned version and hash. It **MUST NOT** be edited by hand.

### **Step 3: Install from the Lockfile with uv pip sync**

To install dependencies into a virtual environment, you **MUST** use uv pip sync with the generated requirements.txt lockfile. This command ensures the environment is an *exact mirror* of the lockfile.

**✅ DO THIS:**

uv pip sync requirements.txt

This is superior to install \-r because it also removes any packages that are not in the lockfile, preventing environment drift.

## **Common Operations**

### **Initial Project Setup (for a new collaborator)**

1. Clone the repository.  
2. Create the virtual environment with uv.  
   uv venv

3. Activate the environment.  
   source .venv/bin/activate  
   \# On Windows: .venv\\Scripts\\activate

4. Install the exact dependencies from the lockfile.  
   uv pip sync requirements.txt

### **Adding a New Package**

1. Manually add the new package name (e.g., polars) to the requirements.in file.  
2. Re-compile the lockfile.  
   uv pip compile requirements.in \-o requirements.txt

3. Sync the environment with the new lockfile.  
   uv pip sync requirements.txt

### **Updating All Packages**

1. To update all packages to their latest allowed versions (according to requirements.in), use the \--upgrade flag during compilation.  
   uv pip compile requirements.in \-o requirements.txt \--upgrade

2. Sync the environment with the updated lockfile.  
   uv pip sync requirements.txt

## **Version Control (GitHub) Policy**

You **MUST** commit both of the following files to the Git repository:

1. **requirements.in**: This tracks the high-level project dependencies that developers manage directly.  
2. **requirements.txt**: This is the generated lockfile that ensures reproducible builds for all collaborators and for CI/CD pipelines.

The .venv directory **MUST** be added to the .gitignore file.

### **❌ Forbidden Commands ❌**

Under this workflow, you **MUST NEVER** use the following commands:

* pip install ...  
* pip freeze ...  
* python \-m venv ...  
* Manually editing requirements.txt.