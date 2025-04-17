import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.Button
import androidx.compose.material.MaterialTheme
import androidx.compose.material.OutlinedTextField
import androidx.compose.material.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import java.io.File
import javax.swing.JFileChooser
import kotlin.concurrent.thread

fun main() = application {
    Window(onCloseRequest = ::exitApplication, title = "YouTube Downloader") {
        MaterialTheme {
            App()
        }
    }
}

@Composable
fun App() {
    var url by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Ready.") }

    Column(modifier = Modifier.padding(16.dp)) {
        Text("YouTube Downloader", style = MaterialTheme.typography.h5)
        OutlinedTextField(value = url, onValueChange = { url = it }, label = { Text("URL") })
        Spacer(Modifier.height(8.dp))
        Button(onClick = {
            status = "Downloading..."
            runDownload(url) {
                status = "Download complete: $it"
                openExplorer(it)
            }
        }) {
            Text("Download")
        }
        Text(status)
    }
}

fun runDownload(url: String, onComplete: (String) -> Unit) {
    thread {
        val outputDir = File("downloads")
        outputDir.mkdirs()
        val cmd = listOf("yt-dlp", "-f", "bestaudio", "-o", "${outputDir.path}/%(title)s.%(ext)s", url)
        val process = ProcessBuilder(cmd)
            .redirectErrorStream(true)
            .start()
        process.inputStream.bufferedReader().lines().forEach { println(it) }
        process.waitFor()

        val downloaded = outputDir.listFiles()?.maxByOrNull { it.lastModified() }?.path ?: "???"
        onComplete(downloaded)
    }
}

fun selectFolder(): File? {
    val dialog = JFileChooser()
    dialog.fileSelectionMode = JFileChooser.DIRECTORIES_ONLY
    dialog.dialogTitle = "Select Download Folder"
    return if (dialog.showOpenDialog(null) == JFileChooser.APPROVE_OPTION) {
        dialog.selectedFile
    } else null
}

fun openExplorer(path: String) {
    val file = File(path)
    if (file.exists()) {
        val command = "explorer /select,\"${file.absolutePath}\""
        Runtime.getRuntime().exec(command)
    }
}
