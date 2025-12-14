const { Sequelize } = require('sequelize');
const path = require('path');

const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: path.join(__dirname, '..', '..', 'database.sqlite'),
  logging: process.env.NODE_ENV === 'development' ? console.log : false,
  define: {
    timestamps: true,
    underscored: true,
  },
});

const initializeDatabase = async () => {
  try {
    await sequelize.authenticate();
    console.log('✓ Database connection established successfully');

    // For SQLite, we need to handle foreign keys carefully during sync
    // Disable foreign key constraints temporarily
    await sequelize.query('PRAGMA foreign_keys = OFF;');

    // Sync all models without altering existing tables
    // This prevents the foreign key constraint errors
    await sequelize.sync({ alter: false });
    console.log('✓ Database models synchronized');

    // Re-enable foreign key constraints
    await sequelize.query('PRAGMA foreign_keys = ON;');

    return true;
  } catch (error) {
    console.error('✗ Unable to connect to the database:', error);
    // Make sure to re-enable foreign keys even if sync fails
    try {
      await sequelize.query('PRAGMA foreign_keys = ON;');
    } catch (e) {
      // Ignore errors when re-enabling foreign keys
    }
    throw error;
  }
};

module.exports = {
  sequelize,
  initializeDatabase,
};
