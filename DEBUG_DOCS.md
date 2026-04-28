# Debug Dev Docs Code Samples

## Step 1: Open Browser Console
Press F12 or right-click → Inspect → Console

## Step 2: Check if elements exist
```javascript
console.log("Quickstart:", document.getElementById("docsSnippetQuickstart"));
console.log("Chat:", document.getElementById("docsSnippetChat"));
console.log("Compare:", document.getElementById("docsSnippetCompare"));
console.log("Memory:", document.getElementById("docsSnippetMemory"));
console.log("Skill:", document.getElementById("docsSnippetSkill"));
```

## Step 3: Check if function exists
```javascript
console.log("Function exists:", typeof renderDocsSnippets);
```

## Step 4: Manually call the function
```javascript
renderDocsSnippets("curl");
```

## Step 5: Check what was rendered
```javascript
const el = document.getElementById("docsSnippetQuickstart");
console.log("Element HTML length:", el.innerHTML.length);
console.log("Element HTML:", el.innerHTML.substring(0, 200));
```
