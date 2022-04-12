package gov.cdc.prime.phdi;

import com.microsoft.azure.functions.annotation.*;
import com.microsoft.azure.functions.*;

/*
package gov.cdc.prime.phdi;

import com.microsoft.azure.functions.annotation.*;
import com.microsoft.azure.functions.*;


public class BlobTriggerJava1 {
    @FunctionName("BlobTriggerJava1")
    @StorageAccount("AzureWebJobsStorage")
    public void run(
        @BlobTrigger(name = "content", path = "samples-workitems/{name}", dataType = "binary") byte[] content,
        @BindingName("name") String name,
        final ExecutionContext context
    ) {
        context.getLogger().info("Java Blob trigger function processed a blob. Name: " + name + "\n  Size: " + content.length + " Bytes");
    }
}

Update `local.settings.json` (`JAVA_HOME` path may vary for local development):
```json
{
  "IsEncrypted": false,
  "Values": {
    "JAVA_HOME": "/usr",
    "FUNCTIONS_WORKER_RUNTIME": "java",
    "FUNCTIONS_EXTENSION_VERSION": "~4",
    "IdConn__blobServiceUri": "https://pidevdatasa.blob.core.windows.net",
    "IdConn__queueServiceUri": "https://pidevdatasa.queue.core.windows.net",
    "AzureWebJobsStorage__accountName": "pitdevdatasa"
  }
}
```

Update extension bundle version in `host.json`:
```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[3.3.0, 4.0.0)"
  } 
}
```

Change storage account variable:
@StorageAccount("AzureWebJobsStorage")
-->
@StorageAccount("AzureWebJobsStorage__accountName")

Add appropriate path and connection name:
@BlobTrigger(name = "content", path = "samples-workitems/{name}", dataType = "binary")
-->
@BlobTrigger(name = "content", path = "silver/{name}", dataType = "binary", connection = "IdConn")

In `pom.xml`, update plugin `com.microsoft.azure` with similar to the following
```xml
<plugin>
    <groupId>com.microsoft.azure</groupId>
    <artifactId>azure-functions-maven-plugin</artifactId>
    <version>${azure.functions.maven.plugin.version}</version>
    <configuration>
        <appName>${functionAppName}</appName>
        <resourceGroup>prime-ingestion-${env}</resourceGroup>
        <appServicePlanName>pi${env}-serviceplan</appServicePlanName>
        <region>eastus</region>
        <deploymentSlot>
            <name>blue</name>
        </deploymentSlot>
        <runtime>
            <os>linux</os>
            <javaVersion>11</javaVersion>
        </runtime>
        <appSettings>
            <property>
                <name>WEBSITE_RUN_FROM_PACKAGE</name>
                <value>1</value>
            </property>
            <property>
                <name>FUNCTIONS_EXTENSION_VERSION</name>
                <value>~4</value>
            </property>
            <property>
                <name>IdConn__blobServiceUri</name>
                <value>https://pi${env}datasa.blob.core.windows.net</value>
            </property>
            <property>
                <name>IdConn__queueServiceUri</name>
                <value>https://pi${env}datasa.queue.core.windows.net</value>
            </property>
            <property>
                <name>AzureWebJobsStorage__accountName</name>
                <value>pi${env}datasa</value>
            </property>
        </appSettings>
    </configuration>
    <executions>
        <execution>
            <id>package-functions</id>
            <goals>
                <goal>package</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

Run the following command to build:
`mvn clean package -DfunctionAppName=pidev-java-functionapp -Denv=dev`

Run the following command to run locally:
`mvn azure-functions:run  -DfunctionAppName=pidev-java-functionapp -Denv=dev`
*/

/**
 * Azure Functions with Azure Blob trigger.
 */
public class BlobTriggerJava1 {
    /**
     * This function will be invoked when a new or updated blob is detected at the specified path. The blob contents are provided as input to this function.
     */
    @FunctionName("BlobTriggerJava1")
    @StorageAccount("AzureWebJobsStorage__accountName")
    public void run(
        @BlobTrigger(name = "content", path = "silver/{name}", dataType = "binary", connection = "IdConn") byte[] content,
        @BindingName("name") String name,
        final ExecutionContext context
    ) {
        context.getLogger().info("Java Blob trigger function processed a blob. Name: " + name + "\n  Size: " + content.length + " Bytes");
    }
}
