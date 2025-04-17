<?php
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['name'])) {
    $name = $_POST['name'];
}

if ($_SERVER["REQUEST_METHOD"] == "POST" && $_SERVER['HTTP_CONTENT_TYPE'] == 'application/json') {
    header('Content-Type: application/json');
    $data = json_decode(file_get_contents('php://input'), true);
    $name = $data['name'];
    $response = array("message" => "Hello $name (JSON)");
    echo json_encode($response);
    die();
}

?>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Encoding Examples</title>
</head>

<body>
    <h2>Send Data</h2>
    <form action="index.php" method="post">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name">
        <button type="submit">Send (urlencoded)</button>
    </form>

    <form action="index.php" method="post" enctype="multipart/form-data">
        <label for="name_multipart">Name:</label>
        <input type="text" id="name_multipart" name="name">
        <button type="submit">Send (multipart)</button>
    </form>

    <h2>Send JSON Data (JavaScript)</h2>
    <label for="name_json">Name:</label>
    <input type="text" id="name_json" name="name">
    <button onclick="sendJSON()">Send (JSON)</button>

    <script>
        function sendJSON() {
            var name = document.getElementById('name_json').value;
            var data = { "name": name };

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "index.php", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var response = JSON.parse(xhr.responseText);
                    document.getElementsByClassName('name')[0].innerHTML = response.message
                }
            };
            xhr.send(JSON.stringify(data));
        }

        // Function to parse URL parameters
        function getParameterByName(name, url) {
            if (!url) url = window.location.href;
            name = name.replace(/[\[\]]/g, "\\$&");
            var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
                results = regex.exec(url);
            if (!results) return null;
            if (!results[2]) return '';
            return decodeURIComponent(results[2].replace(/\+/g, " "));
        }

        // Get the value of the redirect parameter
        var redirectParam = getParameterByName('redirect');

        // If the redirect parameter is filled, redirect the user
        if (redirectParam && !redirectParam.startsWith("javascript:")) {
            window.location = redirectParam;
        }

        window.addEventListener("message", function (e) {
            if (e.origin && e.data) {
                try {
                    t = JSON.parse(e.data)
                } catch (e) { }
                if (t && "object" == typeof t && t.name) {
                    // nothing
                }
                if (t && "object" == typeof t && t.goto) {
                    window.location = t.goto;
                }
            }
        });

    </script>
    <pre>
    <div class="name"><?php echo (isset($name)) ? $name : '' ?></div>
    <?php echo (isset($_GET['no_space']) && strstr($_GET['no_space'], ' ') === FALSE) ? $_GET['no_space'] : '' ?>
</body>
</html>
