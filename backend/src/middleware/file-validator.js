const validateFileUpload = (fieldName, allowedExtensions) => {
  return (req, res, next) => {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: `No ${fieldName} file provided`,
      });
    }

    const fileExtension = req.file.originalname.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(`.${fileExtension}`)) {
      return res.status(400).json({
        success: false,
        message: `Invalid file type. Allowed types: ${allowedExtensions.join(', ')}`,
      });
    }

    next();
  };
};

module.exports = {
  validateFileUpload,
};
