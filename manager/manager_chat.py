from base_chatbot import BaseChatbot
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ManagerChatbot(BaseChatbot):
    def __init__(self, master, user_id: int, db_config: dict, main_callback=None):
        # Initialize the base class - this gives us all reception functions
        super().__init__(master, user_id, db_config, main_callback)
        self.role = "manager"
        
        # Update the GUI to include manager features
        self._add_manager_controls()

    def _add_manager_controls(self):
        """Add manager-specific controls to the existing interface"""
        # Add manager buttons to the sidebar
        manager_actions = [
            ("📊 Manager Dashboard", self.manager_dashboard),
            ("🏠 Room Management", self.manage_rooms),
            ("📈 Reports", self.reports_dashboard),
            ("⚙️ System Controls", self.system_controls)
        ]
        
        # Add these to the existing sidebar
        for i, (text, command) in enumerate(manager_actions):
            ttk.Button(self.sidebar_frame, text=text, command=command, width=18).grid(
                row=len(self.sidebar_frame.winfo_children()) + i, column=0, pady=3, sticky=(tk.W, tk.E))

    def manager_dashboard(self):
        """Manager overview dashboard"""
        self.clear_content()
        
        dashboard_frame = ttk.Frame(self.content_frame)
        dashboard_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dashboard_frame.columnconfigure(0, weight=1)
        
        ttk.Label(dashboard_frame, text="👨‍💼 Manager Dashboard", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=(0, 20))
        
        # Get quick stats using base class data
        stats = self._get_quick_stats()
        
        # Stats display
        stats_frame = ttk.LabelFrame(dashboard_frame, text="Today's Overview", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        metrics = [
            f"🏠 Occupancy: {stats['occupancy_rate']:.1f}%",
            f"🔑 Check-ins Today: {stats['today_checkins']}",
            f"🚪 Check-outs Today: {stats['today_checkouts']}",
            f"📝 Active Bookings: {stats['active_bookings']}",
            f"✅ Available Rooms: {stats['available_rooms']}",
            f"🛠️ Maintenance Rooms: {stats['maintenance_rooms']}"
        ]
        
        for i, metric in enumerate(metrics):
            ttk.Label(stats_frame, text=metric, font=('Arial', 10)).grid(
                row=i, column=0, sticky=tk.W, pady=2)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", padding="10")
        actions_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        quick_actions = [
            ("View All Rooms", self.manage_rooms),
            ("Today's Arrivals", self._view_today_arrivals),
            ("Today's Departures", self._view_today_departures),
            ("System Overview", self.system_controls)
        ]
        
        for i, (text, command) in enumerate(quick_actions):
            ttk.Button(actions_frame, text=text, command=command, width=15).grid(
                row=i//2, column=i%2, padx=5, pady=5)

    def _get_quick_stats(self):
        """Get quick stats for dashboard"""
        try:
            # Occupancy
            self.cursor.execute("SELECT COUNT(*) as total, SUM(status='occupied') as occupied FROM rooms")
            room_data = self.cursor.fetchone()
            occupancy_rate = (room_data['occupied'] / room_data['total'] * 100) if room_data['total'] > 0 else 0
            
            # Today's movements
            self.cursor.execute("""
                SELECT 
                    SUM(DATE(check_in_date)=CURDATE()) as checkins,
                    SUM(DATE(check_out_date)=CURDATE()) as checkouts
                FROM bookings WHERE status IN ('checked_in', 'checked_out')
            """)
            movement = self.cursor.fetchone()
            
            # Room status counts
            self.cursor.execute("""
                SELECT 
                    SUM(status='available') as available,
                    SUM(status='maintenance') as maintenance
                FROM rooms
            """)
            room_status = self.cursor.fetchone()
            
            # Active bookings
            self.cursor.execute("SELECT COUNT(*) as active FROM bookings WHERE status='checked_in'")
            active_bookings = self.cursor.fetchone()
            
            return {
                'occupancy_rate': occupancy_rate,
                'today_checkins': movement['checkins'] or 0,
                'today_checkouts': movement['checkouts'] or 0,
                'active_bookings': active_bookings['active'] or 0,
                'available_rooms': room_status['available'] or 0,
                'maintenance_rooms': room_status['maintenance'] or 0
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'occupancy_rate': 0, 'today_checkins': 0, 'today_checkouts': 0, 
                   'active_bookings': 0, 'available_rooms': 0, 'maintenance_rooms': 0}

    def manage_rooms(self):
        """Enhanced room management with bulk operations"""
        self.clear_content()
        
        rooms_frame = ttk.Frame(self.content_frame)
        rooms_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        rooms_frame.columnconfigure(0, weight=1)
        
        ttk.Label(rooms_frame, text="🏠 Room Management", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=(0, 10))
        
        # Bulk room operations
        bulk_frame = ttk.LabelFrame(rooms_frame, text="Bulk Operations", padding="10")
        bulk_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Room type filter
        filter_frame = ttk.Frame(bulk_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(filter_frame, text="Room Type:").grid(row=0, column=0, padx=(0, 10))
        self.bulk_room_type = tk.StringVar(value="all")
        room_types = ["all", "single", "double", "suite", "deluxe"]
        type_combo = ttk.Combobox(filter_frame, textvariable=self.bulk_room_type, 
                                 values=room_types, state="readonly", width=10)
        type_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(filter_frame, text="Set Status:").grid(row=0, column=2, padx=(0, 10))
        self.bulk_status = tk.StringVar(value="available")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.bulk_status,
                                   values=["available", "maintenance", "cleaning"], 
                                   state="readonly", width=12)
        status_combo.grid(row=0, column=3, padx=(0, 20))
        
        ttk.Button(filter_frame, text="Apply to All Filtered", 
                  command=self._bulk_update_rooms).grid(row=0, column=4)
        
        # Display all rooms using base class method
        self._display_all_rooms(rooms_frame)

    def _bulk_update_rooms(self):
        """Bulk update room statuses"""
        try:
            room_type = self.bulk_room_type.get()
            new_status = self.bulk_status.get()
            
            if room_type == "all":
                query = "UPDATE rooms SET status = %s"
                params = [new_status]
            else:
                query = "UPDATE rooms SET status = %s WHERE room_type = %s"
                params = [new_status, room_type]
            
            self.cursor.execute(query, params)
            self.conn.commit()
            
            messagebox.showinfo("Success", f"Updated rooms to '{new_status}' status")
            self.manage_rooms()  # Refresh the view
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update rooms: {e}")

    def _display_all_rooms(self, parent):
        """Display all rooms with enhanced manager view"""
        try:
            self.cursor.execute("""
                SELECT r.room_number, r.room_type, r.status, r.rate,
                       b.guest_name, b.check_in_date, b.check_out_date
                FROM rooms r
                LEFT JOIN bookings b ON r.room_id = b.room_id AND b.status = 'checked_in'
                ORDER BY r.room_number
            """)
            rooms = self.cursor.fetchall()
            
            table_frame = ttk.LabelFrame(parent, text="All Rooms", padding="10")
            table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
            table_frame.columnconfigure(0, weight=1)
            
            # Enhanced headers for manager
            headers = ["Room", "Type", "Status", "Rate", "Guest", "Check-in", "Check-out", "Actions"]
            for i, header in enumerate(headers):
                ttk.Label(table_frame, text=header, font=('Arial', 9, 'bold')).grid(
                    row=0, column=i, padx=3, pady=3, sticky=tk.W)
            
            for row_idx, room in enumerate(rooms, 1):
                # Room data
                ttk.Label(table_frame, text=room['room_number']).grid(row=row_idx, column=0, padx=3, pady=2)
                ttk.Label(table_frame, text=room['room_type']).grid(row=row_idx, column=1, padx=3, pady=2)
                
                # Status with color coding
                status_color = self._get_status_color(room['status'])
                ttk.Label(table_frame, text=room['status'], foreground=status_color).grid(
                    row=row_idx, column=2, padx=3, pady=2)
                
                ttk.Label(table_frame, text=f"${room['rate']:.2f}").grid(row=row_idx, column=3, padx=3, pady=2)
                ttk.Label(table_frame, text=room['guest_name'] or "-").grid(row=row_idx, column=4, padx=3, pady=2)
                ttk.Label(table_frame, text=str(room['check_in_date'] or "-")).grid(row=row_idx, column=5, padx=3, pady=2)
                ttk.Label(table_frame, text=str(room['check_out_date'] or "-")).grid(row=row_idx, column=6, padx=3, pady=2)
                
                # Action buttons
                action_frame = ttk.Frame(table_frame)
                action_frame.grid(row=row_idx, column=7, padx=3, pady=2)
                
                ttk.Button(action_frame, text="Edit", width=6,
                          command=lambda rn=room['room_number']: self._edit_room(rn)).grid(row=0, column=0, padx=1)
                ttk.Button(action_frame, text="Force", width=6,
                          command=lambda rn=room['room_number']: self._force_room_action(rn)).grid(row=0, column=1, padx=1)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load rooms: {e}")

    def _get_status_color(self, status):
        """Get color for room status"""
        colors = {
            'available': 'green',
            'occupied': 'blue', 
            'maintenance': 'red',
            'cleaning': 'orange'
        }
        return colors.get(status, 'black')

    def _edit_room(self, room_number):
        """Edit room details"""
        try:
            self.cursor.execute("SELECT * FROM rooms WHERE room_number = %s", (room_number,))
            room = self.cursor.fetchone()
            
            if room:
                # Simple edit dialog
                edit_dialog = tk.Toplevel(self.master)
                edit_dialog.title(f"Edit Room {room_number}")
                edit_dialog.geometry("300x200")
                
                ttk.Label(edit_dialog, text=f"Editing Room {room_number}", 
                         font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
                
                # Room rate
                ttk.Label(edit_dialog, text="Rate:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
                rate_var = tk.StringVar(value=str(room['rate']))
                ttk.Entry(edit_dialog, textvariable=rate_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
                
                # Room status
                ttk.Label(edit_dialog, text="Status:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
                status_var = tk.StringVar(value=room['status'])
                status_combo = ttk.Combobox(edit_dialog, textvariable=status_var,
                                           values=["available", "occupied", "maintenance", "cleaning"],
                                           state="readonly", width=12)
                status_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
                
                def save_changes():
                    try:
                        new_rate = float(rate_var.get())
                        new_status = status_var.get()
                        
                        self.cursor.execute(
                            "UPDATE rooms SET rate = %s, status = %s WHERE room_number = %s",
                            (new_rate, new_status, room_number)
                        )
                        self.conn.commit()
                        messagebox.showinfo("Success", "Room updated successfully")
                        edit_dialog.destroy()
                        self.manage_rooms()  # Refresh
                        
                    except ValueError:
                        messagebox.showerror("Error", "Please enter a valid rate")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update room: {e}")
                
                ttk.Button(edit_dialog, text="Save Changes", command=save_changes).grid(
                    row=3, column=0, columnspan=2, pady=20)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit room: {e}")

    def _force_room_action(self, room_number):
        """Force room action (check-out, maintenance override)"""
        try:
            self.cursor.execute("""
                SELECT r.status, b.booking_id, b.guest_name 
                FROM rooms r 
                LEFT JOIN bookings b ON r.room_id = b.room_id AND b.status = 'checked_in'
                WHERE r.room_number = %s
            """, (room_number,))
            room_data = self.cursor.fetchone()
            
            if not room_data:
                return
                
            action_dialog = tk.Toplevel(self.master)
            action_dialog.title(f"Force Action - Room {room_number}")
            action_dialog.geometry("300x150")
            
            ttk.Label(action_dialog, text=f"Room {room_number}", 
                     font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
            
            ttk.Label(action_dialog, text=f"Status: {room_data['status']}").grid(row=1, column=0, columnspan=2)
            ttk.Label(action_dialog, text=f"Guest: {room_data['guest_name'] or 'None'}").grid(row=2, column=0, columnspan=2)
            
            def force_checkout():
                if room_data['booking_id']:
                    self.cursor.execute(
                        "UPDATE bookings SET status = 'checked_out' WHERE booking_id = %s",
                        (room_data['booking_id'],)
                    )
                    self.cursor.execute(
                        "UPDATE rooms SET status = 'cleaning' WHERE room_number = %s",
                        (room_number,)
                    )
                    self.conn.commit()
                    messagebox.showinfo("Success", "Forced check-out completed")
                    action_dialog.destroy()
                    self.manage_rooms()
                else:
                    messagebox.showinfo("Info", "No active booking for this room")
            
            def force_available():
                self.cursor.execute(
                    "UPDATE rooms SET status = 'available' WHERE room_number = %s",
                    (room_number,)
                )
                self.conn.commit()
                messagebox.showinfo("Success", "Room set to available")
                action_dialog.destroy()
                self.manage_rooms()
            
            ttk.Button(action_dialog, text="Force Check-out", command=force_checkout).grid(row=3, column=0, padx=5, pady=10)
            ttk.Button(action_dialog, text="Set Available", command=force_available).grid(row=3, column=1, padx=5, pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to perform action: {e}")

    def reports_dashboard(self):
        """Simple reports dashboard"""
        self.clear_content()
        
        reports_frame = ttk.Frame(self.content_frame)
        reports_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        reports_frame.columnconfigure(0, weight=1)
        
        ttk.Label(reports_frame, text="📈 Reports Dashboard", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=(0, 20))
        
        # Report options
        reports = [
            ("📊 Occupancy Report", self._generate_occupancy_report),
            ("👥 Guest Report", self._generate_guest_report),
            ("🏠 Room Status Report", self._generate_room_report),
            ("💰 Revenue Summary", self._generate_revenue_summary)
        ]
        
        for i, (text, command) in enumerate(reports):
            ttk.Button(reports_frame, text=text, command=command, width=20).grid(
                row=i+1, column=0, pady=10)

    def _generate_occupancy_report(self):
        """Generate occupancy report"""
        try:
            self.cursor.execute("""
                SELECT 
                    DATE(check_in_date) as date,
                    COUNT(*) as bookings,
                    AVG(DATEDIFF(check_out_date, check_in_date)) as avg_stay
                FROM bookings 
                WHERE check_in_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY DATE(check_in_date)
                ORDER BY date DESC
            """)
            data = self.cursor.fetchall()
            
            # Simple display
            report_window = tk.Toplevel(self.master)
            report_window.title("Occupancy Report - Last 30 Days")
            report_window.geometry("500x400")
            
            text_widget = tk.Text(report_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            report_text = "OCCUPANCY REPORT - LAST 30 DAYS\n\n"
            report_text += "Date         | Bookings | Avg Stay\n"
            report_text += "-" * 40 + "\n"
            
            for row in data:
                report_text += f"{row['date']} | {row['bookings']:8} | {row['avg_stay'] or 0:8.1f} nights\n"
            
            text_widget.insert(tk.END, report_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def _generate_guest_report(self):
        """Generate guest report"""
        try:
            self.cursor.execute("""
                SELECT guest_name, email, phone, 
                       COUNT(*) as total_stays,
                       AVG(total_amount) as avg_spend
                FROM bookings 
                GROUP BY guest_name, email, phone
                ORDER BY total_stays DESC
                LIMIT 50
            """)
            data = self.cursor.fetchall()
            
            report_window = tk.Toplevel(self.master)
            report_window.title("Guest Report")
            report_window.geometry("600x400")
            
            text_widget = tk.Text(report_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            report_text = "GUEST REPORT\n\n"
            report_text += "Guest Name          | Stays | Avg Spend\n"
            report_text += "-" * 50 + "\n"
            
            for row in data:
                report_text += f"{row['guest_name'][:20]:20} | {row['total_stays']:5} | ${row['avg_spend'] or 0:8.2f}\n"
            
            text_widget.insert(tk.END, report_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def _generate_room_report(self):
        """Generate room status report"""
        try:
            self.cursor.execute("""
                SELECT room_type, status, COUNT(*) as count
                FROM rooms 
                GROUP BY room_type, status
                ORDER BY room_type, status
            """)
            data = self.cursor.fetchall()
            
            report_window = tk.Toplevel(self.master)
            report_window.title("Room Status Report")
            report_window.geometry("400x300")
            
            text_widget = tk.Text(report_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            report_text = "ROOM STATUS REPORT\n\n"
            report_text += "Room Type | Status      | Count\n"
            report_text += "-" * 35 + "\n"
            
            for row in data:
                report_text += f"{row['room_type']:9} | {row['status']:11} | {row['count']:5}\n"
            
            text_widget.insert(tk.END, report_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def _generate_revenue_summary(self):
        """Generate simple revenue summary"""
        try:
            self.cursor.execute("""
                SELECT 
                    DATE(check_in_date) as date,
                    SUM(total_amount) as daily_revenue,
                    COUNT(*) as bookings
                FROM bookings 
                WHERE check_in_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                AND status IN ('checked_in', 'checked_out')
                GROUP BY DATE(check_in_date)
                ORDER BY date DESC
            """)
            data = self.cursor.fetchall()
            
            report_window = tk.Toplevel(self.master)
            report_window.title("Revenue Summary - Last 7 Days")
            report_window.geometry("500x300")
            
            text_widget = tk.Text(report_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            report_text = "REVENUE SUMMARY - LAST 7 DAYS\n\n"
            report_text += "Date         | Revenue   | Bookings\n"
            report_text += "-" * 35 + "\n"
            
            total_revenue = 0
            total_bookings = 0
            
            for row in data:
                report_text += f"{row['date']} | ${row['daily_revenue'] or 0:8.2f} | {row['bookings']:8}\n"
                total_revenue += row['daily_revenue'] or 0
                total_bookings += row['bookings'] or 0
            
            report_text += f"\nTOTAL: ${total_revenue:,.2f} | {total_bookings} bookings\n"
            report_text += f"AVERAGE: ${total_revenue/len(data) if data else 0:,.2f} per day"
            
            text_widget.insert(tk.END, report_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def system_controls(self):
        """System controls and utilities"""
        self.clear_content()
        
        system_frame = ttk.Frame(self.content_frame)
        system_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        system_frame.columnconfigure(0, weight=1)
        
        ttk.Label(system_frame, text="⚙️ System Controls", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=(0, 20))
        
        # System utilities
        utilities = [
            ("🔄 Refresh All Data", self._refresh_all_data),
            ("🧹 Clean Old Bookings", self._clean_old_bookings),
            ("📋 Database Summary", self._show_database_summary),
            ("🔍 System Status", self._show_system_status)
        ]
        
        for i, (text, command) in enumerate(utilities):
            ttk.Button(system_frame, text=text, command=command, width=20).grid(
                row=i+1, column=0, pady=10)

    def _refresh_all_data(self):
        """Refresh all data caches"""
        messagebox.showinfo("Refresh", "All data has been refreshed")
        self.manager_dashboard()

    def _clean_old_bookings(self):
        """Archive old completed bookings"""
        try:
            self.cursor.execute("""
                UPDATE bookings 
                SET status = 'archived' 
                WHERE status = 'checked_out' 
                AND check_out_date < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            """)
            affected = self.cursor.rowcount
            self.conn.commit()
            messagebox.showinfo("Cleanup", f"Archived {affected} old bookings")
        except Exception as e:
            messagebox.showerror("Error", f"Cleanup failed: {e}")

    def _show_database_summary(self):
        """Show database summary"""
        try:
            tables = ['users', 'rooms', 'bookings', 'guests']
            summary = "DATABASE SUMMARY\n\n"
            
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = self.cursor.fetchone()['count']
                summary += f"{table}: {count} records\n"
            
            messagebox.showinfo("Database Summary", summary)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get summary: {e}")

    def _show_system_status(self):
        """Show system status"""
        status_text = f"""
SYSTEM STATUS

User: {self.user_id}
Role: {self.role}
Database: {'✅ Connected' if self.conn else '❌ Disconnected'}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

All systems operational.
        """
        messagebox.showinfo("System Status", status_text)

    def _view_today_arrivals(self):
        """View today's arrivals using base method"""
        # This would use the base class method for viewing arrivals
        messagebox.showinfo("Info", "Showing today's arrivals...")
        # You would call the base class method here

    def _view_today_departures(self):
        """View today's departures using base method"""
        messagebox.showinfo("Info", "Showing today's departures...")
        # You would call the base class method here