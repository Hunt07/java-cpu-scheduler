module com.cpuscheduler {
    requires javafx.controls;
    requires javafx.graphics;
    requires javafx.base;
    requires java.sql;
    requires java.desktop;
    
    exports com.cpuscheduler.gui;
    exports com.cpuscheduler.model;
}
