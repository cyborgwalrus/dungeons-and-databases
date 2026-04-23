<?php

$adminPassword = getenv('ADMIN_PASSWORD') ?: 'admin';

require_once __DIR__ . '/../plugins/login-password-less.php';

return new AdminerLoginPasswordLess(
    password_hash($adminPassword, PASSWORD_DEFAULT)
);