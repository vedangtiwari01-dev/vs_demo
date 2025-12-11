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

    // Sync all models
    await sequelize.sync({ alter: true });
    console.log('✓ Database models synchronized');

    return true;
  } catch (error) {
    console.error('✗ Unable to connect to the database:', error);
    throw error;
  }
};

module.exports = {
  sequelize,
  initializeDatabase,
};
