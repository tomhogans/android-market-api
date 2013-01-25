CREATE TABLE apk_accounts (
        id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
        username VARCHAR(128) NOT NULL,
        password VARCHAR(32) NOT NULL,
        android_id VARCHAR(32) NOT NULL,
        logins INT(11) UNSIGNED DEFAULT 0,
        downloads INT(11) UNSIGNED DEFAULT 0,
        last_used DATETIME NOT NULL,
        created_at DATETIME NOT NULL,
        PRIMAREY KEY (id),
        UNIQUE KEY (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE apk_apps (
        id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
        package VARCHAR(1024) NOT NULL,
        title VARCHAR(1024) NOT NULL,
        author VARCHAR(1024) NOT NULL,
        ratings_count INT(11) NOT NULL,
        last_version VARCHAR(16) NOT NULL,
        last_fetched DATETIME NOT NULL,
        created_at DATETIME NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY (package)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE apk_requests (
        id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
        account_id INT(11) NOT NULL,
        app_id INT(11) NOT NULL,
        app_version VARCHAR(16) NOT NULL,
        app_file_size INT(11) NOT NULL,
        origin_ip VARCHAR(15) NOT NULL DEFAULT '0.0.0.0',
        created_at DATETIME NOT NULL,
        PRIMARY KEY (id),
        INDEX (account_id),
        INDEX (origin_ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
