# Backend Deployment — Wave D

## Overview

Member 3 is responsible for deploying the CSPM backend API to an Oracle Cloud VM with a managed Neon PostgreSQL database.

## Production Architecture

```text
Frontend (Vercel)
       |
       | HTTPS
       v
Oracle Cloud VM
       |
       +-- FastAPI Backend
       |
       +-- LocalStack
       |
       v
Neon PostgreSQL
- Production authentication cookies are configured with the `Secure` flag.