// import * as React from 'react';
import React from 'react';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import axios from 'axios'
// import logo from './logo.svg';

import {
    BrowserRouter as Router,
    Switch,
    Route,
    Link,
    useLocation,
    useHistory
} from "react-router-dom";

import './App.css';

const { DateTime } = require("luxon");

const DATE_FORMAT = "dd.LL.yyyy"

function valuetext(value) {
    return DateTime.now().minus({ days: -value }).toFormat(DATE_FORMAT);
    // return new Date(new Date().setDate(new Date().getDate() + parseInt(value))).toDateString();
}

function MinimumDistanceSlider(props) {

    const minDistance = 1;

    // const [value2, setValue2] = React.useState([-30, 0]);
    const [value, setValue] = [props.value, props.setValue]

    // transform from date string to relative days
    const value2 = value.map(_date => {
        if (_date != null) {
            return Math.round(DateTime.fromFormat(_date, DATE_FORMAT).diff(DateTime.now().startOf('day'), 'days').as('days'));
        } else {
            return 0;
        }
    });
    // console.log("value",value);
    // transform from relative days to date str
    const setValue2 = function (days) {
        setValue(days.map(day => valuetext(day)));
    };

    const [marks, setMarks] = React.useState([]);


    React.useEffect(() => {
        const fetchData = async () => {
            const result = await axios("/ranges");
            setMarks(result.data.ranges.map(d => {
                return {
                    value: d,
                    label: valuetext(d)
                }
            }));
        };
        fetchData();
    }, []);

    const handleChange2 = (event, newValue, activeThumb) => {
        if (!Array.isArray(newValue)) {
            return;
        }

        if (Math.abs(newValue[1] - newValue[0]) < minDistance) {
            if (activeThumb === 0) {
                const clamped = Math.min(newValue[0], 0 - minDistance);
                setValue2([clamped, clamped + minDistance]);
            } else {
                const clamped = Math.max(newValue[1], -124 + minDistance);
                setValue2([clamped - minDistance, clamped]);
            }
        } else {
            setValue2(newValue);
        }
    };

    return (
        <Slider
            getAriaLabel={() => 'Minimum distance shift'}
            value={value2}
            min={-124}
            max={0}
            marks={marks}
            onChange={handleChange2}
            onChangeCommitted={props.onChangeCommitted}
            valueLabelDisplay="on"
            valueLabelFormat={valuetext}
            disableSwap
        />
    );
}

function ByDayTable(props) {
    // const [data, setData] = React.useState([]);

    // React.useEffect(() => {
    //     if (!('spd_rows' in props.data)) {
    //         return;
    //     }
    //     console.log(props.data)
    //     // setData(props.data['spd_rows']);
    //   }, [props.data]);

    // const data = props.data['spd_rows']
    return (
        <table className="cart">
            <thead>
                <tr>
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((h, inx) =>
                        <td key={inx}>{h}</td>
                    )}
                </tr>
            </thead>

            <tbody>
                {props.data['spd_rows'] && props.data['spd_rows'].map((row, r_inx) =>
                    <tr key={r_inx}>
                        {row.map((r, c_inx) => {
                            const [d, v, com] = r
                            if (d == null) {
                                return <td key={c_inx} />
                            } else {
                                return (
                                    <td key={c_inx} className="hasTooltip">{d} <br />{v}
                                        {com != null && <span className="tooltip" dangerouslySetInnerHTML={{ __html: com }} />}
                                    </td>
                                )
                            }
                        })}
                    </tr>
                )
                }
            </tbody>
        </table>
    );
}

function zip_longest() {
    var args = [].slice.call(arguments);
    var longest = args.reduce(function (a, b) {
        return a.length > b.length ? a : b
    }, []);

    return longest.map(function (_, i) {
        return args.map(function (array) { return array[i] })
    });
}

function SummaryTable(props) {
    const data = props.data;
    return (
        <table className="cart">
            <thead>
                <tr>
                    {data['headers'] && data['headers'].map((h, inx) => {
                        return <td key={inx}>{h}</td>
                    })}
                </tr>
            </thead>

            <tbody>
                {data['rows'] && zip_longest(data['rows'], data['_com']).map((row_row_c, inx_r) => {
                    const [row, row_c] = row_row_c
                    return (
                        <tr key={inx_r}>
                            {zip_longest(row, row_c != null ? row_c : []).map((v_com, c_inx) => {
                                const [v, com] = v_com
                                return (
                                    <td key={c_inx} className="hasTooltip">{v}
                                        {com != null && <span className="tooltip" dangerouslySetInnerHTML={{ __html: com }} />}
                                    </td>
                                )
                            })}
                        </tr>
                    )
                })}
            </tbody>
        </table>
    )
}

function NavTable(props) {
    const data = props.data;

    const onLinkClick = (e) => {
        if (props.onLinkClick != null) {
            props.onLinkClick(e.target.search);
        }
    };

    return (
        <table width="100%">
            <tbody>
                <tr>
                    <td> <Link to={"?after=" + data['prev_after'] + "&before=" + data['prev_before']} onClick={onLinkClick}>Prev Period {data['prev_after']} - {data['prev_before']}</Link> </td>
                </tr>
                <tr>
                    <td> <Link to={"?after=" + data['next_after'] + "&before=" + data['next_before']} onClick={onLinkClick}>Next Period {data['next_after']} - {data['next_before']}</Link> </td>
                </tr>
                <tr>
                    <td> <Link to="/" onClick={onLinkClick}>Last Period</Link> </td>
                </tr>
                <tr>
                    <td> <Link to="/upload" onClick={(e) => { window.location.href = e.target.href }}>Upload</Link> </td>
                </tr>
            </tbody>
        </table>
    )
}


function TabPanel(props) {
    const { children, value, index, ...other } = props;
  
    return (
      <div
        role="tabpanel"
        hidden={value !== index}
        id={`simple-tabpanel-${index}`}
        aria-labelledby={`simple-tab-${index}`}
        {...other}
      >
        {value === index && (
          <Box sx={{ p: 3 }}>
            <Typography>{children}</Typography>
          </Box>
        )}
      </div>
    );
  }
  
//   TabPanel.propTypes = {
//     children: PropTypes.node,
//     index: PropTypes.number.isRequired,
//     value: PropTypes.number.isRequired,
//   };
  
  function a11yProps(index) {
    return {
      id: `simple-tab-${index}`,
      'aria-controls': `simple-tabpanel-${index}`,
    };
  }
  

function Home() {
    const location = useLocation();
    const history = useHistory();

    const query_args = Object.fromEntries(new URLSearchParams(location.search));
    const [slider_value, setSliderValue] = React.useState([query_args['after'], query_args['before']]);

    const onSliderDragStop = () => {
        history.push("?after=" + slider_value[0] + "&before=" + slider_value[1]);
    }

    const [ajax_data, setData] = React.useState(query_args);
    const ajax_query = "/query" + location.search;

    // Tabs
    const [value, setValue] = React.useState(0);

    const handleChange = (event, newValue) => {
      setValue(newValue);
    };
  
    React.useEffect(() => {
        const fetchData = async () => {
            const result = await axios(ajax_query);
            setData(result.data);
            const current_range = [result.data['after'], result.data['before']];
            setSliderValue(current_range);
        };

        fetchData();
    }, [ajax_query]);

    return (
        <Stack spacing={3}>
            <center>Summary {ajax_data['after']} - {ajax_data['before']}</center>
            <Stack direction="row" spacing={1}>
                <Box width={600}>
                    <NavTable data={ajax_data} />
                </Box>
                <MinimumDistanceSlider value={slider_value} setValue={setSliderValue} onChangeCommitted={onSliderDragStop} />
                <Box sx={{ width: 100 }} />
            </Stack>
            <Box sx={{ width: '100%' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={value} onChange={handleChange} aria-label="basic tabs example">
                    <Tab label="Calendar" {...a11yProps(0)} />
                    <Tab label="Summary" {...a11yProps(1)} />
                    <Tab label="Pie Chart" {...a11yProps(2)} />
                    </Tabs>
                </Box>
                <TabPanel value={value} index={0}>
                    <ByDayTable data={ajax_data} />
                </TabPanel>
                <TabPanel value={value} index={1}>
                    <SummaryTable data={ajax_data} />
                </TabPanel>
                <TabPanel value={value} index={3}>
                    <a>Pie chart</a>
                </TabPanel>
            </Box>
        </Stack>
    );
}

function App() {
    return (
        <Router>
            <Switch>
                <Route path="/">
                    <Home />
                </Route>
            </Switch>
        </Router>
    );
}

export default App;
