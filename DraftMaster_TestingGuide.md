---
# 🧪 Draft Master Testing Guide

## 1️⃣ Positive Test Cases

**Test Case ID:** DM_TC_001
**Requirement ID:** DM_REQ_01
**Scenario:** Create draft with valid data
**Steps:**
1. Login as Admin/Editor
2. Navigate to Draft Master
3. Click 'Create Draft'
4. Enter valid Title (<=100 chars), select Category, enter Content
5. Click Save
**Expected Result:** Draft is created, status is 'Draft'

**Test Case ID:** DM_TC_002
**Requirement ID:** DM_REQ_02
**Scenario:** Edit draft with status 'Draft'
**Steps:**
1. Login as Admin/Editor
2. Select a draft with status 'Draft'
3. Edit Title/Content
4. Save changes
**Expected Result:** Changes saved successfully

**Test Case ID:** DM_TC_003
**Requirement ID:** DM_REQ_03
**Scenario:** Delete draft with status 'Draft'
**Steps:**
1. Login as Admin
2. Select a draft with status 'Draft'
3. Click Delete
4. Confirm popup
**Expected Result:** Draft deleted

**Test Case ID:** DM_TC_004
**Requirement ID:** DM_REQ_04
**Scenario:** Search draft by partial title
**Steps:**
1. Enter partial title in search
2. Click Search
**Expected Result:** Matching drafts displayed

**Test Case ID:** DM_TC_005
**Requirement ID:** DM_REQ_05
**Scenario:** Pagination displays 10 records per page
**Steps:**
1. Ensure >10 drafts exist
2. View Draft Master list
**Expected Result:** 10 drafts per page, page numbers shown

---
## 2️⃣ Negative Test Cases

**Test Case ID:** DM_TC_006
**Requirement ID:** DM_REQ_01
**Scenario:** Title > 100 characters
**Steps:**
1. Enter title with 101+ characters
2. Click Save
**Expected Result:** Error: "Title cannot exceed 100 characters."

**Test Case ID:** DM_TC_007
**Requirement ID:** DM_REQ_01
**Scenario:** Empty Title
**Steps:**
1. Leave Title empty
2. Click Save
**Expected Result:** Error: "Title is required."

**Test Case ID:** DM_TC_008
**Requirement ID:** DM_REQ_01
**Scenario:** Empty Content
**Steps:**
1. Leave Content empty
2. Click Save
**Expected Result:** Error: "Content cannot be empty."

**Test Case ID:** DM_TC_009
**Requirement ID:** DM_REQ_02
**Scenario:** Try editing published draft
**Steps:**
1. Select draft with status 'Published'
2. Try to edit
**Expected Result:** Edit not allowed

**Test Case ID:** DM_TC_010
**Requirement ID:** DM_REQ_03
**Scenario:** Delete published draft
**Steps:**
1. Select draft with status 'Published'
2. Click Delete
**Expected Result:** Delete not allowed

**Test Case ID:** DM_TC_011
**Requirement ID:** DM_REQ_01
**Scenario:** Category not selected
**Steps:**
1. Leave Category unselected
2. Click Save
**Expected Result:** Error: "Category must be selected."

**Test Case ID:** DM_TC_012
**Requirement ID:** DM_REQ_01
**Scenario:** Special character <script> in Title/Content
**Steps:**
1. Enter <script> in Title/Content
2. Click Save
**Expected Result:** Error: "Invalid input format."

---
## 3️⃣ Requirement Traceability Matrix (RTM)

| Requirement ID | Test Case ID | Status |
| -------------- | ------------ | ------ |
| DM_REQ_01      | DM_TC_001    | Pass   |
| DM_REQ_01      | DM_TC_006    | Pass   |
| DM_REQ_01      | DM_TC_007    | Pass   |
| DM_REQ_01      | DM_TC_008    | Pass   |
| DM_REQ_01      | DM_TC_011    | Pass   |
| DM_REQ_01      | DM_TC_012    | Pass   |
| DM_REQ_02      | DM_TC_002    | Pass   |
| DM_REQ_02      | DM_TC_009    | Pass   |
| DM_REQ_03      | DM_TC_003    | Pass   |
| DM_REQ_03      | DM_TC_010    | Pass   |
| DM_REQ_04      | DM_TC_004    | Pass   |
| DM_REQ_05      | DM_TC_005    | Pass   |

---
## 4️⃣ Clarification Questions for Developer

1. What are the allowed values for Category? Is it fixed or dynamic?
2. Should drafts auto-save or only save on user action?
3. Is there a maximum length for Content?
4. What happens if a Viewer tries to access Draft Master?
5. Is there an audit log for create/edit/delete actions?
6. Should deleted drafts be recoverable (soft delete) or permanently removed?
7. Are there any restrictions on file attachments in drafts?
8. Should the system support bulk actions (delete/edit multiple drafts)?
9. Is there a limit to the number of drafts a user can create?
10. What is the expected behavior if page load exceeds 3 seconds?
