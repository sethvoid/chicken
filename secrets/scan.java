import java.io.IOException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class CommentScanner {

    public static Map<Integer, String> extractHtmlComments(String content, String url) {
        Map<Integer, String> htmlComments = new HashMap<>();

        Pattern pattern = Pattern.compile("<!--(.*?)-->", Pattern.DOTALL);
        Matcher matcher = pattern.matcher(content);
        while (matcher.find()) {
            String comment = matcher.group(1).trim();
            htmlComments.put(matcher.start() + 1, url.isEmpty() ? comment : url + " " + comment);
        }

        return htmlComments;
    }

    public static Map<Integer, Map<Integer, String>> extractJsComments(String content) {
        Map<Integer, Map<Integer, String>> jsComments = new HashMap<>();
        Pattern scriptPattern = Pattern.compile("<script[^>]*>(.*?)</script>", Pattern.DOTALL | Pattern.CASE_INSENSITIVE);
        Matcher scriptMatcher = scriptPattern.matcher(content);

        while (scriptMatcher.find()) {
            Map<Integer, String> scriptComments = new HashMap<>();
            String scriptContent = scriptMatcher.group(1);
            Scanner scanner = new Scanner(scriptContent);

            int lineCounter = 1;
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                Pattern commentPattern = Pattern.compile("//(.*?)$|/\\*(.*?)\\*/");
                Matcher commentMatcher = commentPattern.matcher(line);
                while (commentMatcher.find()) {
                    String comment = commentMatcher.group(1) != null ? commentMatcher.group(1) : commentMatcher.group(2);
                    scriptComments.put(lineCounter, comment.trim());
                }
                lineCounter++;
            }
            jsComments.put(scriptMatcher.start() + "<script>".length(), scriptComments);
            scanner.close();
        }
        return jsComments;
    }

    public static Map<Integer, String> scanForProhibited(Map<Integer, String> htmlComments, Map<Integer, Map<Integer, String>> jsComments) {
        Map<Integer, String> prohibitedFindings = new HashMap<>();
        try {
            Scanner scanner = new Scanner(CommentScanner.class.getResourceAsStream("prohib.json"), "UTF-8");
            StringBuilder jsonBuilder = new StringBuilder();
            while (scanner.hasNextLine()) {
                jsonBuilder.append(scanner.nextLine());
            }
            scanner.close();
            String jsonContent = jsonBuilder.toString();
            // Parse JSON content
            // Assuming JSON is in the format: [{"prohib1": "value1"}, {"prohib2": "value2"}, ...]
            // Adjust this according to the actual format of your JSON
            // Here I'm assuming each entry is a Map with a single key-value pair
            String[] entries = jsonContent.split(",");
            for (String entry : entries) {
                String[] parts = entry.split(":");
                String prohibitedWord = parts[0].trim().replaceAll("[\"{}]", "");
                String value = parts[1].trim().replaceAll("[\"{}]", "");
                for (Map.Entry<Integer, String> htmlEntry : htmlComments.entrySet()) {
                    if (htmlEntry.getValue().toLowerCase().contains(value.toLowerCase())) {
                        prohibitedFindings.put(htmlEntry.getKey(), "PROHIBITED VALUE (" + prohibitedWord + ") in comment " + htmlEntry.getValue());
                    }
                }
                for (Map.Entry<Integer, Map<Integer, String>> scriptEntry : jsComments.entrySet()) {
                    for (Map.Entry<Integer, String> scriptCommentEntry : scriptEntry.getValue().entrySet()) {
                        if (scriptCommentEntry.getValue().toLowerCase().contains(value.toLowerCase())) {
                            prohibitedFindings.put(scriptEntry.getKey() + scriptCommentEntry.getKey() - 1, "PROHIBITED VALUE (" + prohibitedWord + ") in comment " + scriptCommentEntry.getValue());
                        }
                    }
                }
            }
        } catch (IOException e) {
            System.out.println("Error: Could not find prohib.json file");
        }
        return prohibitedFindings;
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java scan <url>");
            System.exit(1);
        }

        String url = args[0];
        try {
            Scanner scanner = new Scanner(new URL(url).openStream(), "UTF-8").useDelimiter("\\A");
            String content = scanner.hasNext() ? scanner.next() : "";
            scanner.close();

            Map<Integer, String> htmlComments = extractHtmlComments(content, url);
            for (Map.Entry<Integer, String> entry : htmlComments.entrySet()) {
                System.out.println("[" + entry.getKey() + "] " + entry.getValue());
            }

            Map<Integer, Map<Integer, String>> jsComments = extractJsComments(content);
            for (Map.Entry<Integer, Map<Integer, String>> scriptEntry : jsComments.entrySet()) {
                int scriptLocation = scriptEntry.getKey();
                Map<Integer, String> scriptComments = scriptEntry.getValue();
                for (Map.Entry<Integer, String> commentEntry : scriptComments.entrySet()) {
                    int line = commentEntry.getKey();
                    String comment = commentEntry.getValue();
                    System.out.println("[Script location: " + scriptLocation + ", Line: " + line + "] " + comment);
                }
            }

            Map<Integer, String> prohibitedFindings = scanForProhibited(htmlComments, jsComments);
            if (!prohibitedFindings.isEmpty()) {
                System.out.println("\n**************** PROHIBITED COMMENTS DISCOVERED ****************");
                for (Map.Entry<Integer, String> entry : prohibitedFindings.entrySet()) {
                    System.out.println(entry.getValue());
                }
            }
        } catch (IOException e) {
            System.out.println("Error: Could not retrieve content from URL: " + e.getMessage());
            System.exit(1);
        }
    }
}
