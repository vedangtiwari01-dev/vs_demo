/**
 * Database Fix Script
 * Cleans up backup tables and fixes foreign key constraints
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'database.sqlite');

console.log('Opening database:', dbPath);
console.log('Database path:', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
    process.exit(1);
  }

  console.log('✓ Database opened successfully');

  // First, disable foreign key constraints
  db.run('PRAGMA foreign_keys = OFF', (err) => {
    if (err) {
      console.error('✗ Error disabling foreign keys:', err.message);
      db.close();
      process.exit(1);
    }

    console.log('✓ Disabled foreign key constraints');

    // Drop all backup tables
    const backupTables = [
      'sops_backup',
      'workflow_logs_backup',
      'sop_rules_backup',
      'officers_backup',
      'deviations_backup',
      'behavioral_profiles_backup',
      'behavioral_patterns_backup',
      'stress_test_scenarios_backup'
    ];

    let completed = 0;
    backupTables.forEach(tableName => {
      db.run(`DROP TABLE IF EXISTS ${tableName}`, (err) => {
        if (err) {
          console.error(`✗ Error dropping ${tableName}:`, err.message);
        } else {
          console.log(`✓ Dropped ${tableName} (if it existed)`);
        }

        completed++;
        if (completed === backupTables.length) {
          // Re-enable foreign key constraints
          db.run('PRAGMA foreign_keys = ON', (err) => {
            if (err) {
              console.error('✗ Error re-enabling foreign keys:', err.message);
            } else {
              console.log('✓ Re-enabled foreign key constraints');
            }

            db.close((err) => {
              if (err) {
                console.error('Error closing database:', err.message);
              } else {
                console.log('\n✓ Database fix complete!');
                console.log('✓ All backup tables removed');
                console.log('✓ You can now restart the backend with: npm start');
              }
            });
          });
        }
      });
    });
  });
});
