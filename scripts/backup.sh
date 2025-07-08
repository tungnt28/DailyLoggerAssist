#!/bin/bash

# Daily Logger Assist Database Backup Script
# This script creates automated backups of the PostgreSQL database

set -e

# Configuration
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-dailylogger}"
DB_USER="${POSTGRES_USER:-dailylogger}"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/dailylogger_backup_${DATE}.sql"
COMPRESSED_BACKUP="${BACKUP_FILE}.gz"

# Retention settings
RETAIN_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "Starting backup of Daily Logger Assist database..."
echo "Date: $(date)"
echo "Database: ${DB_NAME}"
echo "Host: ${DB_HOST}"

# Create database backup
echo "Creating database dump..."
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --verbose --clean --no-owner --no-privileges \
    --format=plain > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "Database dump created successfully: ${BACKUP_FILE}"
    
    # Compress the backup
    echo "Compressing backup..."
    gzip "${BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        echo "Backup compressed successfully: ${COMPRESSED_BACKUP}"
        
        # Verify the compressed backup
        echo "Verifying compressed backup..."
        zcat "${COMPRESSED_BACKUP}" | head -n 10 > /dev/null
        
        if [ $? -eq 0 ]; then
            echo "Backup verification successful"
            
            # Calculate backup size
            BACKUP_SIZE=$(du -h "${COMPRESSED_BACKUP}" | cut -f1)
            echo "Backup size: ${BACKUP_SIZE}"
            
            # Clean up old backups
            echo "Cleaning up backups older than ${RETAIN_DAYS} days..."
            find "${BACKUP_DIR}" -name "dailylogger_backup_*.sql.gz" -mtime +${RETAIN_DAYS} -delete
            
            # Log backup success
            echo "Backup completed successfully at $(date)"
            echo "Backup file: ${COMPRESSED_BACKUP}"
            
        else
            echo "ERROR: Backup verification failed"
            rm -f "${COMPRESSED_BACKUP}"
            exit 1
        fi
    else
        echo "ERROR: Backup compression failed"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi
else
    echo "ERROR: Database dump failed"
    exit 1
fi

echo "Backup process completed successfully" 