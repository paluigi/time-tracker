import flet
from flet import (
    Page,
    Text,
    Column,
    Container,
    Row,
    VerticalDivider,
    IconButton,
    SnackBar,
    TextField,
    Button,
    Icons,
    DatePicker,
    DataTable,
    DataColumn,
    DataRow,
    DataCell,
    AlertDialog,
    Dropdown,
    dropdown,
    TextButton,
    OutlinedButton,
    Card,
    Markdown,
    FilePicker,
    InputFilter,
    border,
    Border,
)
from datetime import datetime, date
from db_operations import Database
import polars as pl
import tempfile
import os


class Application:
    def __init__(self):
        self.current_view = "projects"
        self.db = Database()
        self.current_project = None
        self.current_entry = None
        self.editing_entry = False
        self.from_date = None
        self.to_date = None
        
        # Form fields
        self.project_name_field = None
        self.entry_date_picker = None
        self.entry_hours_field = None
        self.entry_description_field = None
        self.date_field = None
        
        # Dialog references
        self.entry_dialog = None
        self.confirm_delete_entry_dialog = None
        self.confirm_delete_project_dialog = None
        
        # Report fields
        self.report_project_dropdown = None
        self.report_from_date_picker = None
        self.report_to_date_picker = None
        self.report_content = None
    
    async def main(self, page: Page):
        """Main entry point for Flet application."""
        self.page = page
        
        # Configure page
        self.page.title = "Time Tracker"
        self.page.window_width = 1000
        self.page.window_height = 700
        self.page.scroll = "auto"
        self.page.padding = 10
        self.page.theme_mode = "light"
        
        # Initialize database
        await self.db.initialize()
        
        # Build navigation bar
        self.navbar = Row(
            [
                IconButton(Icons.FOLDER, on_click=lambda e: self.show_projects_view(), tooltip="Projects"),
                IconButton(Icons.ASSIGNMENT, on_click=lambda e: self.show_report_view(), tooltip="Reports"),
            ],
            alignment="spaceBetween",
        )
        
        # Initialize content container
        self.content = Container()
        
        # Add main layout to page
        self.page.add(
            Column(
                [
                    self.navbar,
                    VerticalDivider(),
                    self.content,
                ],
                expand=True,
            )
        )
        
        # Show initial view
        self.show_projects_view()
    
    def update_content(self, content):
        """Update the main content area."""
        self.content.content = content
        self.content.update()
    
    def show_snack_bar(self, message: str):
        """Display a snack bar message."""
        snackbar = SnackBar(Text(message))
        self.page.show_dialog(snackbar)
    
    # ==================== PROJECTS VIEW ====================
    
    def show_create_project_dialog(self, e):
        """Show dialog to create a new project."""
        # Create a new TextField instance
        self.project_name_field = TextField(
            label="Project Name",
            hint_text="Enter project name...",
            autofocus=True,
        )
        
        # Create dialog
        dialog = AlertDialog(
            title=Text("Create New Project"),
            content=Column([self.project_name_field], tight=True),
            actions=[
                TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                Button("Create", on_click=lambda e: self.create_project(dialog, e)),
            ],
        )
        
        self.page.show_dialog(dialog)
    
    def show_projects_view(self):
        """Display the projects list view."""
        self.current_view = "projects"
        
        # Get all projects
        projects = self.db.get_all_projects()
        
        # Build project list
        project_rows = []
        for project in projects:
            project_id, project_name, created_at = project
            # Get entry count and total hours
            entries = self.db.get_entries_for_project(project_id)
            total_hours = sum(entry[2] for entry in entries)
            
            project_card = Card(
                content=Container(
                    Column(
                        [
                            Row(
                                [
                                    Text(project_name, size=20, weight="bold", expand=True),
                                    Text(f"{len(entries)} entries", size=14, color="grey"),
                                ],
                                alignment="spaceBetween"
                            ),
                            Row(
                                [
                                    Text(f"Total: {total_hours:.1f} hours", size=14),
                                    Container(expand=True),
                                    IconButton(Icons.VISIBILITY, on_click=lambda e, pid=project_id: self.view_project_detail(pid)),
                                    IconButton(Icons.EDIT, on_click=lambda e, pid=project_id: self.edit_project(pid)),
                                    IconButton(Icons.DELETE, on_click=lambda e, pid=project_id: self.confirm_delete_project(pid)),
                                ],
                                alignment="spaceBetween"
                            )
                        ],
                        spacing=5,
                        tight=True
                    ),
                    padding=15,
                    width=500
                )
            )
            project_rows.append(project_card)
        
        if not project_rows:
            project_rows.append(Text("No projects yet. Create your first project!", color="grey"))
        
        self.update_content(
            Container(
                Column(
                    [
                        Text("Projects", size=28, weight="bold"),
                        Row(
                            [
                                OutlinedButton(
                                    "Create New Project",
                                    icon=Icons.ADD,
                                    on_click=self.show_create_project_dialog
                                ),
                            ],
                            alignment="start"
                        ),
                        Container(height=20),
                        Column(project_rows, spacing=10, scroll="auto"),
                    ],
                    scroll="auto",
                ),
                padding=20,
            )
        )
    
    def create_project(self, dialog, e):
        """Create a new project."""
        project_name = self.project_name_field.value.strip()
        
        if not project_name:
            self.show_snack_bar("Please enter a project name")
            return
        
        try:
            self.db.create_project(project_name)
            dialog.open = False
            self.page.update()
            self.show_projects_view()
            self.show_snack_bar(f"Project '{project_name}' created successfully")
        except Exception as ex:
            self.show_snack_bar(f"Error creating project: {str(ex)}")
    
    def edit_project(self, project_id: int):
        """Edit a project name."""
        project = self.db.get_project(project_id)
        if not project:
            return
        
        self.project_name_field = TextField(
            label="Project Name",
            value=project[1],
            autofocus=True,
        )
        
        self.current_project = project_id
        
        dialog = AlertDialog(
            title=Text("Edit Project"),
            content=Column([self.project_name_field], tight=True),
            actions=[
                TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                Button("Save", on_click=lambda e: self.update_project(dialog, e)),
            ],
        )
        
        self.page.show_dialog(dialog)
    
    def update_project(self, dialog, e):
        """Update project name."""
        project_name = self.project_name_field.value.strip()
        
        if not project_name:
            self.show_snack_bar("Please enter a project name")
            return
        
        try:
            self.db.update_project(self.current_project, project_name)
            dialog.open = False
            self.page.update()
            self.show_projects_view()
            self.show_snack_bar(f"Project updated successfully")
        except Exception as ex:
            self.show_snack_bar(f"Error updating project: {str(ex)}")
    
    def confirm_delete_project(self, project_id: int):
        """Show confirmation dialog for project deletion."""
        project = self.db.get_project(project_id)
        if not project:
            return
        
        self.current_project = project_id
        
        self.confirm_delete_project_dialog = AlertDialog(
            title=Text("Delete Project"),
            content=Text(f"Are you sure you want to delete '{project[1]}'? All entries will be deleted too."),
            actions=[
                TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                Button("Delete", icon=Icons.DELETE, on_click=lambda e: self.delete_project(e), bgcolor="red"),
            ],
        )
        
        self.page.show_dialog(self.confirm_delete_project_dialog)
    
    def delete_project(self, e):
        """Delete a project."""
        try:
            self.db.delete_project(self.current_project)
            self.close_dialog()
            self.show_projects_view()
            self.show_snack_bar(f"Project deleted successfully")
        except Exception as ex:
            self.show_snack_bar(f"Error deleting project: {str(ex)}")
    
    def close_dialog(self):
        """Close current dialog."""
        self.page.pop_dialog()
    
    # ==================== PROJECT DETAIL VIEW ====================
    
    def view_project_detail(self, project_id: int):
        """Show project detail with entries."""
        self.current_project = project_id
        project = self.db.get_project(project_id)
        
        if not project:
            self.show_snack_bar("Project not found")
            return
        
        project_name = project[1]
        entries = self.db.get_entries_for_project(project_id)
        total_hours = sum(entry[2] for entry in entries)
        
        # Build entries table
        entry_rows = []
        for entry in entries:
            entry_id, entry_date, hours, description, created_at = entry
            entry_rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(entry_date)),
                        DataCell(Text(f"{hours:.1f}")),
                        DataCell(Text(description or "", max_lines=2, overflow="ellipsis")),
                        DataCell(
                            Row(
                                [
                                    IconButton(Icons.EDIT, icon_size=20, on_click=lambda e, eid=entry_id: self.edit_entry(eid)),
                                    IconButton(Icons.DELETE, icon_size=20, on_click=lambda e, eid=entry_id: self.confirm_delete_entry(eid)),
                                ]
                            )
                        ),
                    ]
                )
            )
        
        if not entry_rows:
            entry_rows.append(
                DataRow(
                    cells=[
                        DataCell(Text("No entries yet", color="grey")),
                        DataCell(Text("")),
                        DataCell(Text("")),
                        DataCell(Text("")),
                    ]
                )
            )
        
        self.update_content(
            Container(
                Column(
                    [
                        Row(
                            [
                                IconButton(Icons.ARROW_BACK, on_click=lambda e: self.show_projects_view()),
                                Text(project_name, size=24, weight="bold", expand=True),
                            ]
                        ),
                        Row(
                            [
                                Text(f"{len(entries)} entries", size=14, color="grey"),
                                Text(f"Total: {total_hours:.1f} hours", size=14, color="grey"),
                                Container(expand=True),
                                OutlinedButton(
                                    "Add Entry",
                                    icon=Icons.ADD,
                                    on_click=lambda e: self.show_create_entry_dialog()
                                ),
                            ],
                            alignment="spaceBetween"
                        ),
                        Container(height=20),
                        DataTable(
                            columns=[
                                DataColumn(Text("Date")),
                                DataColumn(Text("Hours")),
                                DataColumn(Text("Description"), numeric=False),
                                DataColumn(Text("Actions")),
                            ],
                            rows=entry_rows,
                            border=Border.all(2, "grey"),
                            horizontal_margin=10,
                            data_row_max_height=100,
                            width=800,
                            show_bottom_border=True,
                        ),
                    ],
                    scroll="auto",
                ),
                padding=20,
            )
        )
    
    # ==================== ENTRY FORM ====================
    
    def show_create_entry_dialog(self):
        """Show dialog to create a new entry."""
        self.editing_entry = False
        self.entry_date_picker = DatePicker(value=datetime.now())
        self.entry_hours_field = TextField(
            label="Hours",
            hint_text="e.g., 2.5",
            keyboard_type="number",
            input_filter=InputFilter(regex_string=r"[0-9.]*")
        )
        self.entry_description_field = TextField(label="Description", hint_text="What did you work on?", max_lines=3)
        
        self.date_field = TextField(
            label="Date",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=200
        )
        
        def handle_date_change(e):
            """Handle date picker change."""
            if self.entry_date_picker.value:
                self.date_field.value = self.entry_date_picker.value.strftime("%Y-%m-%d")
                self.date_field.update()
        
        self.entry_date_picker.on_change = handle_date_change
        
        self.entry_dialog = AlertDialog(
            title=Text("Add Time Entry"),
            content=Column(
                [
                    Row(
                        [
                            self.date_field,
                            OutlinedButton(
                                content=Text("Select Date"),
                                icon=Icons.CALENDAR_MONTH,
                                on_click=lambda e: self.page.show_dialog(self.entry_date_picker),
                            ),
                        ],
                        alignment="spaceBetween"
                    ),
                    self.entry_hours_field,
                    self.entry_description_field,
                ],
                tight=True,
                scroll="auto"
            ),
            actions=[
                TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                Button("Save", on_click=lambda e: self.save_entry(e)),
            ],
        )
        
        self.page.show_dialog(self.entry_dialog)
    
    def update_date_button(self, e):
        """Update the date button text when a date is selected."""
        if e.control.value:
            dialog = self.page.dialog
            # Find and update the date button
            for control in dialog.content.controls:
                if isinstance(control, OutlinedButton):
                    control.text = f"Select Date: {e.control.value}"
                    control.update()
    
    def save_entry(self, e):
        """Save a new or updated entry."""
        entry_date = self.entry_date_picker.value
        hours = self.entry_hours_field.value
        description = self.entry_description_field.value
        
        if not entry_date:
            self.show_snack_bar("Please select a date")
            return
        
        if not hours:
            self.show_snack_bar("Please enter hours")
            return
        
        try:
            hours_float = float(hours)
            if hours_float <= 0:
                self.show_snack_bar("Hours must be greater than 0")
                return
        except ValueError:
            self.show_snack_bar("Please enter a valid number for hours")
            return
        
        try:
            date_str = entry_date.strftime("%Y-%m-%d")
            if self.editing_entry:
                self.db.update_entry(self.current_entry, date_str, hours_float, description)
                self.show_snack_bar("Entry updated successfully")
            else:
                self.db.create_entry(self.current_project, date_str, hours_float, description)
                self.show_snack_bar("Entry created successfully")
            
            self.entry_dialog.open = False
            self.page.update()
            self.view_project_detail(self.current_project)
        except Exception as ex:
            self.show_snack_bar(f"Error saving entry: {str(ex)}")
    
    def edit_entry(self, entry_id: int):
        """Edit an existing entry."""
        entry = self.db.get_entry(entry_id)
        if not entry:
            return
        
        self.editing_entry = True
        self.current_entry = entry_id
        
        entry_date = datetime.strptime(entry[2], "%Y-%m-%d")
        
        self.entry_date_picker = DatePicker(value=entry_date)
        self.entry_hours_field = TextField(
            label="Hours",
            value=str(entry[3]),
            keyboard_type="number",
            input_filter=InputFilter(regex_string=r"[0-9.]*")
        )
        self.entry_description_field = TextField(label="Description", value=entry[4] or "", max_lines=3)
        
        self.date_field = TextField(
            label="Date",
            value=entry_date.strftime("%Y-%m-%d"),
            width=200
        )
        
        def handle_date_change(e):
            """Handle date picker change."""
            if self.entry_date_picker.value:
                self.date_field.value = self.entry_date_picker.value.strftime("%Y-%m-%d")
                self.date_field.update()
        
        self.entry_date_picker.on_change = handle_date_change
        
        self.entry_dialog = AlertDialog(
            title=Text("Edit Time Entry"),
            content=Column(
                [
                    Row(
                        [
                            self.date_field,
                            OutlinedButton(
                                content=Text("Select Date"),
                                icon=Icons.CALENDAR_MONTH,
                                on_click=lambda e: self.page.show_dialog(self.entry_date_picker),
                            ),
                        ],
                        alignment="spaceBetween"
                    ),
                    self.entry_hours_field,
                    self.entry_description_field,
                ],
                tight=True,
                scroll="auto"
            ),
            actions=[
                TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                Button("Save", on_click=lambda e: self.save_entry(e)),
            ],
        )
        
        self.page.show_dialog(self.entry_dialog)
    
    def confirm_delete_entry(self, entry_id: int):
        """Show confirmation dialog for entry deletion."""
        self.current_entry = entry_id
        
        self.confirm_delete_entry_dialog = AlertDialog(
            title=Text("Delete Entry"),
            content=Text("Are you sure you want to delete this entry?"),
            actions=[
                TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                Button("Delete", icon=Icons.DELETE, on_click=lambda e: self.delete_entry(e), bgcolor="red"),
            ],
        )
        
        self.page.show_dialog(self.confirm_delete_entry_dialog)
    
    def delete_entry(self, e):
        """Delete an entry."""
        try:
            self.db.delete_entry(self.current_entry)
            self.close_dialog()
            self.view_project_detail(self.current_project)
            self.show_snack_bar("Entry deleted successfully")
        except Exception as ex:
            self.show_snack_bar(f"Error deleting entry: {str(ex)}")
    
    # ==================== REPORT VIEW ====================
    
    def show_report_view(self):
        """Display the report generation view."""
        self.current_view = "report"
        
        # Get all projects for dropdown
        projects = self.db.get_all_projects()
        project_options = [("Select Project", None)] + [(p[1], p[0]) for p in projects]
        
        self.report_project_dropdown = Dropdown(
            label="Project",
            options=[dropdown.Option(value, label) for label, value in project_options]
        )
        
        self.report_from_date_picker = DatePicker()
        self.report_to_date_picker = DatePicker()
        
        self.report_from_date_picker.on_change = self._update_from_date
        self.report_to_date_picker.on_change = self._update_to_date
        
        self.report_content = Container(
            Text("Select a project to generate a report", color="grey")
        )
        
        self.update_content(
            Container(
                Column(
                    [
                        Text("Reports", size=28, weight="bold"),
                        Row(
                            [
                                self.report_project_dropdown,
                            ],
                            alignment="start"
                        ),
                        Row(
                            [
                                OutlinedButton(
                                    f"From: {self.from_date.strftime('%Y-%m-%d') if self.from_date else 'Any'}",
                                    icon=Icons.CALENDAR_MONTH,
                                    on_click=lambda e: self.pick_from_date(),
                                ),
                                OutlinedButton(
                                    f"To: {self.to_date.strftime('%Y-%m-%d') if self.to_date else 'Any'}",
                                    icon=Icons.CALENDAR_MONTH,
                                    on_click=lambda e: self.pick_to_date(),
                                ),
                                Container(expand=True),
                                OutlinedButton(
                                    "Generate Report",
                                    icon=Icons.ANALYTICS,
                                    on_click=lambda e: self.generate_report(),
                                ),
                                OutlinedButton(
                                    "Export Excel",
                                    icon=Icons.DOWNLOAD,
                                    on_click=self.handle_export_excel,
                                ),
                            ],
                            alignment="spaceBetween"
                        ),
                        Container(height=20),
                        self.report_content,
                    ],
                    scroll="auto",
                ),
                padding=20,
            )
        )
    
    def on_project_change(self, e):
        """Handle project dropdown change."""
        pass
    
    def _update_from_date(self, e):
        """Update from date when date picker changes."""
        if e.control.value:
            self.from_date = e.control.value
            self.show_report_view()  # Refresh to show new date
    
    def _update_to_date(self, e):
        """Update to date when date picker changes."""
        if e.control.value:
            self.to_date = e.control.value
            self.show_report_view()  # Refresh to show new date
    
    def pick_from_date(self):
        """Pick from date for report filter."""
        self.page.show_dialog(self.report_from_date_picker)
    
    def pick_to_date(self):
        """Pick to date for report filter."""
        self.page.show_dialog(self.report_to_date_picker)
    
    async def handle_export_excel(self, e):
        """Async wrapper for export to Excel button handler."""
        await self.export_to_excel()
    
    def generate_report(self):
        """Generate report using Polars and display as DataTable."""
        project_id = self.report_project_dropdown.value
        
        if not project_id:
            self.show_snack_bar("Please select a project")
            return
        
        project = self.db.get_project(project_id)
        if not project:
            return
        
        # Get filtered entries
        from_date_str = self.from_date.strftime("%Y-%m-%d") if self.from_date else None
        to_date_str = self.to_date.strftime("%Y-%m-%d") if self.to_date else None
        
        entries = self.db.get_entries_for_project(project_id, from_date_str, to_date_str)
        
        if not entries:
            self.report_content.content = Text("No entries found for the selected criteria", color="grey")
            self.report_content.update()
            return
        
        # Convert to Polars DataFrame
        df = pl.DataFrame({
            "Date": [entry[1] for entry in entries],
            "Hours": [entry[2] for entry in entries],
            "Description": [entry[3] or "" for entry in entries],
        })
        
        # Calculate total hours
        total_hours = df["Hours"].sum()
        
        # Build entries table rows
        entry_rows = []
        for entry in entries:
            entry_rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(entry[1])),
                        DataCell(Text(f"{entry[2]:.1f}")),
                        DataCell(Text(entry[3] or "", max_lines=2, overflow="ellipsis")),
                    ]
                )
            )
        
        # Display as DataTable with summary statistics above
        self.report_content.content = Column(
            [
                Text(f"Report: {project[1]}", size=20, weight="bold"),
                Container(height=10),
                Row(
                    [
                        Text(f"Total Entries: {len(entries)}", size=14, color="grey"),
                        Text(f"Total Hours: {total_hours:.1f}", size=14, color="grey"),
                    ],
                    alignment="spaceBetween"
                ),
                Container(height=20),
                DataTable(
                    columns=[
                        DataColumn(Text("Date")),
                        DataColumn(Text("Hours")),
                        DataColumn(Text("Description"), numeric=False),
                    ],
                    rows=entry_rows,
                    border=Border.all(2, "grey"),
                    horizontal_margin=10,
                    data_row_max_height=100,
                    width=800,
                    show_bottom_border=True,
                ),
            ],
            scroll="auto"
        )
        
        # Store current data for export
        self.current_report_data = (df, project[1])
        
        self.report_content.update()
    
    async def export_to_excel(self):
        """Export report to Excel."""
        if not hasattr(self, 'current_report_data'):
            self.show_snack_bar("Please generate a report first")
            return
        
        df, project_name = self.current_report_data
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Write to Excel using openpyxl
            df.write_excel(tmp_path)
            
            # Open file picker to save using new Flet pattern
            save_path = await FilePicker().save_file(
                dialog_title="Save Report",
                file_name=f"{project_name}_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                initial_directory=os.path.expanduser("~")
            )
            
            if save_path:
                # Copy temporary file to chosen location
                import shutil
                shutil.copy2(tmp_path, save_path)
                self.show_snack_bar(f"Report exported to {save_path}")
            else:
                self.show_snack_bar("Export cancelled")
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
        except Exception as ex:
            self.show_snack_bar(f"Error exporting to Excel: {str(ex)}")


if __name__ == '__main__':
    app = Application()
    flet.run(main=app.main)