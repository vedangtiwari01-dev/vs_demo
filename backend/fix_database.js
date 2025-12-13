/**
 * Database Fix Script
 * Drops the sops_backup table to allow migrations to proceed
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'database.sqlite');

console.log('Opening database:', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
    process.exit(1);
  }

  console.log('✓ Database opened successfully');

  // Drop the backup table if it exists
  db.run('DROP TABLE IF EXISTS sops_backup', (err) => {
    if (err) {
      console.error('✗ Error dropping backup table:', err.message);
      db.close();
      process.exit(1);
    }

    console.log('✓ Dropped sops_backup table (if it existed)');

    // Also drop workflow_logs_backup if it exists
    db.run('DROP TABLE IF EXISTS workflow_logs_backup', (err) => {
      if (err) {
        console.error('✗ Error dropping workflow backup table:', err.message);
        db.close();
        process.exit(1);
      }

      console.log('✓ Dropped workflow_logs_backup table (if it existed)');

      db.close((err) => {
        if (err) {
          console.error('Error closing database:', err.message);
        } else {
          console.log('\n✓ Database fix complete!');
          console.log('✓ You can now restart the backend with: npm start');
        }
      });
    });
  });
});
