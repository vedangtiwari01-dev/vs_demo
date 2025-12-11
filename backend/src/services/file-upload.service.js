const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = file.fieldname === 'sop' ? 'uploads/sops' : 'uploads/logs';
    cb(null, path.join(__dirname, '..', '..', dir));
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    const ext = path.extname(file.originalname);
    const basename = path.basename(file.originalname, ext);
    cb(null, `${basename}-${uniqueSuffix}${ext}`);
  }
});

const fileFilter = (req, file, cb) => {
  const allowedTypes = {
    sop: ['.pdf', '.docx'],
    logs: ['.csv', '.json']
  };

  const ext = path.extname(file.originalname).toLowerCase();
  const fieldName = file.fieldname;

  if (allowedTypes[fieldName] && allowedTypes[fieldName].includes(ext)) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type. Allowed: ${allowedTypes[fieldName].join(', ')}`), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE) || 50 * 1024 * 1024, // 50MB default
  },
});

const deleteFile = async (filePath) => {
  try {
    await fs.unlink(filePath);
    return true;
  } catch (error) {
    console.error('Error deleting file:', error);
    return false;
  }
};

module.exports = {
  upload,
  deleteFile,
};
